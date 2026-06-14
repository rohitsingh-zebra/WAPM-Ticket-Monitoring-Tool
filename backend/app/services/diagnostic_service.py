from __future__ import annotations

import re
import socket
from datetime import datetime, timezone
from stat import S_ISREG
from typing import Callable

import paramiko

from app.config import Settings
from app.models import DiagnosticFile, DiagnosticInvalidFile, DiagnosticPrecheckResponse, DiagnosticRunResponse, Ticket
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
            files, invalid_files = self._list_and_validate_remote_files(host_name=host_name, otp=otp.strip())
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
        except UploadScriptReadError:
            return DiagnosticRunResponse(
                success=False,
                error_code="UPLOADDATA_SCRIPT_READ_FAILED",
                message="Unable to read or parse uploaddata.sh for allowed file formats.",
                company=company,
                host_name=host_name,
                remote_path=self.settings.diagnostic_remote_path,
            )

        total_file_count = len(files)
        invalid_file_count = len(invalid_files)
        valid_file_count = total_file_count - invalid_file_count

        return DiagnosticRunResponse(
            success=True,
            message="Diagnostic completed successfully.",
            company=company,
            host_name=host_name,
            remote_path=self.settings.diagnostic_remote_path,
            file_count=total_file_count,
            files=files,
            total_file_count=total_file_count,
            valid_file_count=valid_file_count,
            invalid_file_count=invalid_file_count,
            invalid_files=invalid_files,
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

    def _list_and_validate_remote_files(
        self,
        host_name: str,
        otp: str,
    ) -> tuple[list[DiagnosticFile], list[DiagnosticInvalidFile]]:
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
            invalid_files: list[DiagnosticInvalidFile] = []
            if len(files) > self.settings.diagnostic_max_file_count:
                allowed_extensions = self._extract_allowed_extensions_from_script(sftp)
                invalid_files = self._find_invalid_files(files, allowed_extensions)
            return files, invalid_files
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

    def _extract_allowed_extensions_from_script(self, sftp: paramiko.SFTPClient) -> set[str]:
        try:
            with sftp.file(self.settings.diagnostic_uploaddata_script_path, "r") as script_file:
                content = script_file.read()
        except OSError as exc:
            raise UploadScriptReadError(str(exc)) from exc

        try:
            script_text = content.decode("utf-8")
        except UnicodeDecodeError:
            script_text = content.decode("latin-1")

        tokens = re.findall(r"\*\.[^\s`]+", script_text)
        allowed_extensions: set[str] = set()
        for token in tokens:
            normalized = self._token_to_extension(token)
            if normalized:
                allowed_extensions.add(normalized)

        if not allowed_extensions:
            raise UploadScriptReadError("No allowed file formats were parsed from script.")
        return allowed_extensions

    def _token_to_extension(self, token: str) -> str | None:
        suffix = token[2:] if token.startswith("*.") else token
        if not suffix:
            return None
        idx = 0
        chars: list[str] = []
        while idx < len(suffix):
            char = suffix[idx]
            if char == "[":
                closing = suffix.find("]", idx + 1)
                if closing == -1:
                    return None
                group = suffix[idx + 1 : closing]
                if not group:
                    return None
                chars.append(group[0].lower())
                idx = closing + 1
                continue
            if char.isalnum():
                chars.append(char.lower())
            idx += 1
        return "".join(chars) or None

    def _find_invalid_files(
        self,
        files: list[DiagnosticFile],
        allowed_extensions: set[str],
    ) -> list[DiagnosticInvalidFile]:
        rules: list[tuple[str, Callable[[str, set[str]], bool]]] = [
            ("WHITESPACE_IN_FILENAME", self._has_whitespace),
            ("UNSUPPORTED_FORMAT", self._has_unsupported_extension),
        ]
        invalid_files: list[DiagnosticInvalidFile] = []
        for file in files:
            for reason, rule in rules:
                if rule(file.name, allowed_extensions):
                    invalid_files.append(DiagnosticInvalidFile(name=file.name, reason=reason))
                    break
        return invalid_files

    def _has_whitespace(self, file_name: str, _allowed_extensions: set[str]) -> bool:
        return any(char.isspace() for char in file_name)

    def _has_unsupported_extension(self, file_name: str, allowed_extensions: set[str]) -> bool:
        extension = file_name.rsplit(".", maxsplit=1)[-1].lower() if "." in file_name else ""
        return extension not in allowed_extensions


class ServerConnectionError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InvalidOtpError(Exception):
    pass


class UploadScriptReadError(Exception):
    pass

