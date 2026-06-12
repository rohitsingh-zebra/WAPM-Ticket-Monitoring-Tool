from __future__ import annotations

import socket
from datetime import datetime, timezone
from stat import S_ISREG

import paramiko

from app.config import Settings
from app.models import DiagnosticFile, DiagnosticPrecheckResponse, DiagnosticRunResponse, Ticket
from app.services.company_host import COMPANY_HOSTS


class DiagnosticService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run_for_ticket(self, ticket: Ticket, otp: str) -> DiagnosticRunResponse:
        precheck = self.precheck_ticket(ticket)
        if not precheck.success:
            return DiagnosticRunResponse(
                success=False,
                error_code=precheck.error_code,
                message=precheck.message,
                company=precheck.company,
            )

        company = precheck.company
        host_name = precheck.host_name

        try:
            files = self._list_remote_files(host_name=host_name, otp=otp.strip())
        except InvalidCredentialsError:
            return DiagnosticRunResponse(
                success=False,
                error_code="INVALID_CREDENTIALS",
                message="Please check GCP username and password in the .env file and update correctly.",
                company=company,
                host_name=host_name,
                remote_path=self.settings.diagnostic_remote_path,
            )
        except InvalidOtpError:
            return DiagnosticRunResponse(
                success=False,
                error_code="INVALID_OTP",
                message="Second password/OTP is invalid. Please enter second password again.",
                company=company,
                host_name=host_name,
                remote_path=self.settings.diagnostic_remote_path,
            )
        except ServerConnectionError:
            return DiagnosticRunResponse(
                success=False,
                error_code="HOST_CONNECTION_FAILED",
                message="Unable to connect to app server. Please check if host name is correct.",
                company=company,
                host_name=host_name,
                remote_path=self.settings.diagnostic_remote_path,
            )

        return DiagnosticRunResponse(
            success=True,
            message="Diagnostic completed successfully.",
            company=company,
            host_name=host_name,
            remote_path=self.settings.diagnostic_remote_path,
            file_count=len(files),
            files=files,
        )

    def precheck_ticket(self, ticket: Ticket) -> DiagnosticPrecheckResponse:
        company = self._extract_company(ticket.organization)
        if not company:
            return DiagnosticPrecheckResponse(
                success=False,
                error_code="HOSTNAME_MAPPING_NOT_FOUND",
                message="No mapping of hostname found for client UNKNOWN. Please update mapping of hostname.",
            )

        host_name = COMPANY_HOSTS.get(company.upper())
        if not host_name:
            return DiagnosticPrecheckResponse(
                success=False,
                error_code="HOSTNAME_MAPPING_NOT_FOUND",
                message=f"No mapping of hostname found for client {company}. Please update mapping of hostname.",
                company=company,
            )

        return DiagnosticPrecheckResponse(
            success=True,
            message="Hostname mapping found. Please enter second password/OTP to continue.",
            company=company,
            host_name=host_name,
        )

    def _extract_company(self, organization: str) -> str | None:
        text = (organization or "").strip()
        if not text:
            return None

        first = text.split("-", maxsplit=1)[0].strip()
        if not first:
            return None
        return first.split()[0].upper()

    def _list_remote_files(self, host_name: str, otp: str) -> list[DiagnosticFile]:
        if not otp:
            raise InvalidOtpError("Missing OTP")

        sock = None
        transport = None
        sftp = None
        try:
            sock = socket.create_connection((host_name, self.settings.diagnostic_ssh_port), timeout=15)
            transport = paramiko.Transport(sock)
            transport.start_client(timeout=15)

            # WinSCP-like behavior for your environment: total password = base password + OTP.
            combined_password = f"{self.settings.gcp_password}{otp}"
            combined_auth_failed = False
            try:
                transport.auth_password(self.settings.gcp_username, combined_password)
            except paramiko.AuthenticationException:
                combined_auth_failed = True

            if not transport.is_authenticated():
                try:
                    transport.auth_password(self.settings.gcp_username, self.settings.gcp_password)
                except paramiko.ssh_exception.PartialAuthentication:
                    # Base password accepted, server expects another factor.
                    pass
                except paramiko.AuthenticationException as exc:
                    # If combined failed and base password also fails, credentials are likely wrong.
                    if combined_auth_failed:
                        raise InvalidCredentialsError(str(exc)) from exc
                    raise

            if not transport.is_authenticated():
                try:
                    transport.auth_interactive(
                        self.settings.gcp_username,
                        lambda _title, _instructions, prompts: self._interactive_handler(prompts, otp),
                    )
                except paramiko.AuthenticationException as exc:
                    raise InvalidOtpError(str(exc)) from exc

            if not transport.is_authenticated():
                raise InvalidOtpError("OTP authentication failed")

            sftp = paramiko.SFTPClient.from_transport(transport)
            entries = sftp.listdir_attr(self.settings.diagnostic_remote_path)

            files = [
                DiagnosticFile(
                    name=entry.filename,
                    modified_at=datetime.fromtimestamp(entry.st_mtime, tz=timezone.utc),
                )
                for entry in entries
                if S_ISREG(entry.st_mode)
            ]
            files.sort(key=lambda item: item.modified_at, reverse=True)
            return files
        except (socket.gaierror, socket.timeout, TimeoutError, OSError, paramiko.SSHException) as exc:
            if isinstance(exc, (InvalidCredentialsError, InvalidOtpError)):
                raise
            raise ServerConnectionError(str(exc)) from exc
        finally:
            if sftp is not None:
                sftp.close()
            if transport is not None:
                transport.close()
            if sock is not None:
                sock.close()

    def _interactive_handler(self, prompts: list[tuple[str, bool]], otp: str) -> list[str]:
        responses: list[str] = []
        for prompt, _echo in prompts:
            prompt_lower = prompt.lower()
            if "password" in prompt_lower and "second" not in prompt_lower and "otp" not in prompt_lower:
                responses.append(self.settings.gcp_password)
            elif "otp" in prompt_lower or "second" in prompt_lower or "token" in prompt_lower or "verification" in prompt_lower:
                responses.append(otp)
            else:
                responses.append(otp)
        return responses


class ServerConnectionError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InvalidOtpError(Exception):
    pass

