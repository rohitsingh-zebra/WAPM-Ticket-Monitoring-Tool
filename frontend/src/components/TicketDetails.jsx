import { useEffect, useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Link from "@mui/material/Link";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";

import { precheckDiagnostic, runDiagnostic } from "../api/client";

const formatDate = (value) => {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
};

const formatDateUtc = (value) => {
  if (!value) {
    return "-";
  }
  return `${new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(new Date(value))} UTC`;
};

const statusClassName = (status) => {
  const normalizedStatus = status?.toLowerCase() ?? "";
  if (normalizedStatus.includes("to do") || normalizedStatus.includes("open")) {
    return "status-chip status-todo";
  }
  if (normalizedStatus.includes("progress")) {
    return "status-chip status-progress";
  }
  if (normalizedStatus.includes("resolved") || normalizedStatus.includes("closed") || normalizedStatus.includes("done")) {
    return "status-chip status-resolved";
  }
  return "status-chip";
};

function TicketDetails({ ticket }) {
  const [otp, setOtp] = useState("");
  const [precheckResult, setPrecheckResult] = useState(null);
  const [diagnosticResult, setDiagnosticResult] = useState(null);

  useEffect(() => {
    setOtp("");
    setPrecheckResult(null);
    setDiagnosticResult(null);
  }, [ticket?.key]);

  const precheckMutation = useMutation({
    mutationFn: (ticketId) => precheckDiagnostic(ticketId),
    onSuccess: (data) => {
      setPrecheckResult(data);
      setDiagnosticResult(null);
    },
    onError: (error) => {
      const message = error.response?.data?.detail ?? error.message ?? "Failed to check hostname mapping.";
      setPrecheckResult({
        success: false,
        message,
      });
      setDiagnosticResult(null);
    },
  });

  const diagnosticMutation = useMutation({
    mutationFn: ({ ticketId, secondPassword }) =>
      runDiagnostic({
        ticketId,
        otp: secondPassword,
      }),
    onSuccess: (data) => {
      setDiagnosticResult(data);
    },
    onError: (error) => {
      const message = error.response?.data?.detail ?? error.message ?? "Failed to run diagnostic.";
      setDiagnosticResult({
        success: false,
        message,
      });
    },
  });

  const hasBlockingOtpError = useMemo(
    () => diagnosticResult?.error_code === "INVALID_OTP",
    [diagnosticResult],
  );

  if (!ticket) {
    return null;
  }

  return (
    <Stack spacing={1.5}>
      <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
        <Typography variant="h6">{ticket.key}</Typography>
        <Chip label={ticket.status} size="small" className={statusClassName(ticket.status)} />
      </Stack>
      <Typography fontWeight={600}>{ticket.summary}</Typography>
      <Box>
        <Typography variant="body2" color="text.secondary">
          Issue Category
        </Typography>
        <Typography>{ticket.category}</Typography>
      </Box>
      <Box>
        <Typography variant="body2" color="text.secondary">
          cluster_id / clientId Env
        </Typography>
        <Typography>
          {ticket.cluster} / {ticket.organization}
        </Typography>
      </Box>
      <Box>
        <Typography variant="body2" color="text.secondary">
          Assignee
        </Typography>
        <Typography>{ticket.assignee ?? "Unassigned"}</Typography>
      </Box>
      <Box>
        <Typography variant="body2" color="text.secondary">
          Created / Updated
        </Typography>
        <Typography>
          {formatDate(ticket.created)} / {formatDate(ticket.updated)}
        </Typography>
      </Box>
      <Box>
        <Typography variant="body2" color="text.secondary">
          Resolution Time
        </Typography>
        <Typography>
          {ticket.resolution_time_hours !== null && ticket.resolution_time_hours !== undefined
            ? `${ticket.resolution_time_hours} hours`
            : "Not resolved"}
        </Typography>
      </Box>
      <Link href={ticket.jira_url} target="_blank" rel="noreferrer">
        Open in Jira
      </Link>
      <Box className="diagnostic-box">
        <Typography variant="subtitle2" fontWeight={700} sx={{ mb: 1 }}>
          Run Diagnostic
        </Typography>
        <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
          <Button
            variant="contained"
            disabled={precheckMutation.isPending || diagnosticMutation.isPending}
            onClick={() => precheckMutation.mutate(ticket.key)}
          >
            {precheckMutation.isPending ? "Checking..." : "Run"}
          </Button>
        </Stack>
        {precheckMutation.isPending && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Checking client hostname mapping...
          </Typography>
        )}
        {precheckResult && (
          <Alert severity={precheckResult.success ? "success" : "error"} sx={{ mt: 1 }}>
            {precheckResult.message}
          </Alert>
        )}
        {precheckResult?.success && (
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1} sx={{ mt: 1 }}>
            <TextField
              label="Please enter second password / OTP"
              value={otp}
              size="small"
              fullWidth
              error={hasBlockingOtpError}
              helperText={hasBlockingOtpError ? "Please enter the correct second password/OTP." : " "}
              onChange={(event) => setOtp(event.target.value)}
            />
            <Button
              variant="outlined"
              disabled={diagnosticMutation.isPending || otp.trim().length === 0}
              onClick={() => diagnosticMutation.mutate({ ticketId: ticket.key, secondPassword: otp.trim() })}
              sx={{
                minWidth: 80,
                borderRadius: "8px",
                px: 2,
                py: 0.35,
                minHeight: 34,
                textTransform: "none",
                fontWeight: 700,
                whiteSpace: "nowrap",
              }}
            >
              {diagnosticMutation.isPending ? "Submitting..." : "Submit"}
            </Button>
          </Stack>
        )}
        {diagnosticMutation.isPending && (
          <Stack direction="row" spacing={1} sx={{ mt: 1, alignItems: "center" }}>
            <CircularProgress size={16} />
            <Typography variant="body2" color="text.secondary">
              Connecting to app server and reading files...
            </Typography>
          </Stack>
        )}

        {diagnosticResult && precheckResult?.success && (
          <Stack spacing={1} sx={{ mt: 1 }}>
            <Alert severity={diagnosticResult.success ? "success" : "error"}>{diagnosticResult.message}</Alert>

            {diagnosticResult.success && (
              <>
                <Typography variant="body2" color="text.secondary">
                  Host: {diagnosticResult.host_name} | Path: {diagnosticResult.remote_path}
                </Typography>
                <Typography variant="body2" fontWeight={700}>
                  Files Found: {diagnosticResult.file_count}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Times shown in UTC
                </Typography>
                <Box className="diagnostic-file-list">
                  <Box className="diagnostic-file-table">
                    {diagnosticResult.file_count > 0 && (
                      <Box className="diagnostic-file-row diagnostic-file-row--header">
                        <Typography variant="caption" className="diagnostic-file-name">
                          File Name
                        </Typography>
                        <Typography variant="caption" className="diagnostic-file-time">
                          Changed (UTC)
                        </Typography>
                      </Box>
                    )}
                    {(diagnosticResult.files ?? []).map((file) => (
                      <Box key={`${file.name}-${file.modified_at}`} className="diagnostic-file-row">
                        <Typography variant="body2" fontWeight={600} className="diagnostic-file-name">
                          {file.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" className="diagnostic-file-time">
                          {formatDateUtc(file.modified_at)}
                        </Typography>
                      </Box>
                    ))}
                    {diagnosticResult.file_count === 0 && (
                      <Typography variant="body2" color="text.secondary" sx={{ p: 1.25 }}>
                        No files found in the configured folder.
                      </Typography>
                    )}
                  </Box>
                </Box>
              </>
            )}
          </Stack>
        )}
      </Box>
    </Stack>
  );
}

export default TicketDetails;
