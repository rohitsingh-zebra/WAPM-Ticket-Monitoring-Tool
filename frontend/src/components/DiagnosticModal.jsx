import { useEffect, useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import CloseIcon from "@mui/icons-material/Close";
import FilterListIcon from "@mui/icons-material/FilterList";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Dialog from "@mui/material/Dialog";
import IconButton from "@mui/material/IconButton";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";

import { precheckDiagnostic, runDiagnostic } from "../api/client";

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

function DiagnosticModal({ ticket, open, onClose }) {
  const [otp, setOtp] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [nameSort, setNameSort] = useState("asc");
  const [dateSort, setDateSort] = useState("desc");
  const [primarySort, setPrimarySort] = useState("date");
  const [precheckResult, setPrecheckResult] = useState(null);
  const [diagnosticResult, setDiagnosticResult] = useState(null);
  const [nameMenuAnchor, setNameMenuAnchor] = useState(null);
  const [dateMenuAnchor, setDateMenuAnchor] = useState(null);
  const [invalidModalOpen, setInvalidModalOpen] = useState(false);

  const resetState = () => {
    setOtp("");
    setSearchTerm("");
    setNameSort("asc");
    setDateSort("desc");
    setPrimarySort("date");
    setPrecheckResult(null);
    setDiagnosticResult(null);
    setNameMenuAnchor(null);
    setDateMenuAnchor(null);
    setInvalidModalOpen(false);
  };

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
        error_code: null,
        message,
      });
    },
  });

  useEffect(() => {
    if (!open || !ticket?.key) {
      resetState();
      return;
    }
    resetState();
    precheckMutation.mutate(ticket.key);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, ticket?.key]);

  const isOtpVisible = precheckResult?.success && !diagnosticResult?.success;

  const files = diagnosticResult?.success ? diagnosticResult.files ?? [] : [];
  const invalidFiles = diagnosticResult?.success ? diagnosticResult.invalid_files ?? [] : [];
  const filteredAndSortedFiles = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();
    const filtered = normalizedSearch
      ? files.filter((file) => file.name.toLowerCase().includes(normalizedSearch))
      : files;

    const compareByName = (a, b) => {
      const nameCompare = a.name.localeCompare(b.name, undefined, { sensitivity: "base" });
      return nameSort === "asc" ? nameCompare : -nameCompare;
    };
    const compareByDate = (a, b) => {
      const dateCompare = new Date(a.modified_at).getTime() - new Date(b.modified_at).getTime();
      return dateSort === "asc" ? dateCompare : -dateCompare;
    };

    return [...filtered].sort((a, b) => {
      if (primarySort === "name") {
        const byName = compareByName(a, b);
        if (byName !== 0) {
          return byName;
        }
        return compareByDate(a, b);
      }
      const byDate = compareByDate(a, b);
      if (byDate !== 0) {
        return byDate;
      }
      return compareByName(a, b);
    });
  }, [dateSort, files, nameSort, primarySort, searchTerm]);

  const handleDialogClose = (_event, reason) => {
    if (reason === "backdropClick") {
      return;
    }
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={handleDialogClose}
      maxWidth={false}
      fullWidth
      sx={{
        "& .MuiDialog-paper": {
          width: "60vw !important",
          minWidth: "60vw !important",
          maxWidth: "60vw !important",
          height: "80vh !important",
          minHeight: "80vh !important",
          maxHeight: "80vh !important",
          margin: "0 !important",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        },
      }}
      PaperProps={{
        className: "diagnostic-modal-paper",
      }}
    >
      <Box className="diagnostic-modal-header">
        <Typography variant="h6" fontWeight={800}>
          Run Diagnostic - {ticket?.key}
        </Typography>
        <IconButton onClick={onClose} aria-label="Close diagnostic modal">
          <CloseIcon />
        </IconButton>
      </Box>

      <Box className="diagnostic-modal-status-box">
        {precheckMutation.isPending && (
          <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
            <CircularProgress size={16} />
            <Typography variant="body2">Checking client hostname mapping...</Typography>
          </Stack>
        )}

        {precheckResult && !(precheckResult.success && diagnosticResult?.success) && (
          <Alert severity={precheckResult.success ? "success" : "error"}>{precheckResult.message}</Alert>
        )}

        {precheckResult?.success && (
          <Typography variant="body2" color="text.secondary">
            Hostname: {precheckResult.host_name}
          </Typography>
        )}

        {isOtpVisible && (
          <>
            <Stack direction={{ xs: "column", md: "row" }} spacing={1} sx={{ alignItems: { md: "flex-start" } }}>
              <Box sx={{ flex: 1 }}>
                <TextField
                  label="Please enter second password / OTP"
                  value={otp}
                  size="small"
                  fullWidth
                  error={diagnosticResult?.error_code === "INVALID_OTP"}
                  onChange={(event) => setOtp(event.target.value)}
                />
              </Box>
              <Button
                size="small"
                variant="contained"
                disabled={diagnosticMutation.isPending || otp.trim().length === 0}
                onClick={() => diagnosticMutation.mutate({ ticketId: ticket.key, secondPassword: otp.trim() })}
                sx={{
                  minWidth: 92,
                  height: 40,
                  borderRadius: "8px",
                  textTransform: "none",
                  fontWeight: 700,
                  px: 1.2,
                  lineHeight: 1.15,
                  whiteSpace: "nowrap",
                }}
              >
                {diagnosticMutation.isPending ? "Submitting..." : "Submit"}
              </Button>
            </Stack>
            {diagnosticResult?.error_code === "INVALID_OTP" && (
              <Typography variant="caption" color="error" sx={{ mt: -0.5 }}>
                Please enter correct second password/OTP.
              </Typography>
            )}
          </>
        )}

        {diagnosticMutation.isPending && (
          <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
            <CircularProgress size={16} />
            <Typography variant="body2">Connecting to app server and reading files...</Typography>
          </Stack>
        )}

        {diagnosticResult && (
          <Alert severity={diagnosticResult.success ? "success" : "error"}>{diagnosticResult.message}</Alert>
        )}
      </Box>

      <Box className="diagnostic-modal-table-shell">
        {diagnosticResult?.success ? (
          <>
            <Box className="diagnostic-modal-table-toolbar">
              <Stack spacing={0.6}>
                <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
                  <Typography variant="body2" fontWeight={700}>
                    Files Found: {diagnosticResult.file_count}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Times shown in UTC
                  </Typography>
                </Stack>
                <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                  <Typography variant="caption" color="text.secondary">
                    Found {diagnosticResult.invalid_file_count ?? 0} invalid files (checks run when files older than{" "}
                    {diagnosticResult.stuck_threshold_hours ?? 24}h exceed{" "}
                    {diagnosticResult.max_diagnostic_file_count ?? 50} files)
                  </Typography>
                  <Button
                    size="small"
                    variant="outlined"
                    disabled={invalidFiles.length === 0}
                    onClick={() => setInvalidModalOpen(true)}
                  >
                    Open Invalid Files
                  </Button>
                </Stack>
              </Stack>
              <TextField
                size="small"
                label="Search file name"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                sx={{ minWidth: 250 }}
              />
            </Box>

            <Box className="diagnostic-modal-table-scroll">
              <Box className="diagnostic-modal-table">
                <Box className="diagnostic-modal-row diagnostic-modal-row--header">
                  <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
                    <Typography variant="caption" fontWeight={700}>
                      File Name
                    </Typography>
                    <IconButton size="small" onClick={(event) => setNameMenuAnchor(event.currentTarget)}>
                      <FilterListIcon fontSize="inherit" />
                    </IconButton>
                  </Stack>
                  <Stack direction="row" spacing={0.5} sx={{ alignItems: "center", justifyContent: "flex-start" }}>
                    <Typography variant="caption" fontWeight={700}>
                      Changed (UTC)
                    </Typography>
                    <IconButton size="small" onClick={(event) => setDateMenuAnchor(event.currentTarget)}>
                      <FilterListIcon fontSize="inherit" />
                    </IconButton>
                  </Stack>
                </Box>

                {filteredAndSortedFiles.map((file) => (
                  <Box key={`${file.name}-${file.modified_at}`} className="diagnostic-modal-row">
                    <Typography variant="body2" className="diagnostic-modal-file-name">
                      {file.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" className="diagnostic-modal-file-time">
                      {formatDateUtc(file.modified_at)}
                    </Typography>
                  </Box>
                ))}

                {filteredAndSortedFiles.length === 0 && (
                  <Box className="diagnostic-modal-empty-row">
                    <Typography variant="body2" color="text.secondary">
                      No files match the current search/filter.
                    </Typography>
                  </Box>
                )}
              </Box>
            </Box>
          </>
        ) : (
          <Box className="diagnostic-modal-table-empty" />
        )}
      </Box>

      <Menu anchorEl={nameMenuAnchor} open={Boolean(nameMenuAnchor)} onClose={() => setNameMenuAnchor(null)}>
        <MenuItem
          onClick={() => {
            setNameSort("asc");
            setPrimarySort("name");
            setNameMenuAnchor(null);
          }}
        >
          A to Z
        </MenuItem>
        <MenuItem
          onClick={() => {
            setNameSort("desc");
            setPrimarySort("name");
            setNameMenuAnchor(null);
          }}
        >
          Z to A
        </MenuItem>
      </Menu>

      <Menu anchorEl={dateMenuAnchor} open={Boolean(dateMenuAnchor)} onClose={() => setDateMenuAnchor(null)}>
        <MenuItem
          onClick={() => {
            setDateSort("desc");
            setPrimarySort("date");
            setDateMenuAnchor(null);
          }}
        >
          Newest to Oldest
        </MenuItem>
        <MenuItem
          onClick={() => {
            setDateSort("asc");
            setPrimarySort("date");
            setDateMenuAnchor(null);
          }}
        >
          Oldest to Newest
        </MenuItem>
      </Menu>

      <Dialog
        open={invalidModalOpen}
        onClose={() => setInvalidModalOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{ className: "diagnostic-invalid-modal-paper" }}
      >
        <Box className="diagnostic-modal-header">
          <Typography variant="h6" fontWeight={800}>
            Invalid Files - {ticket?.key}
          </Typography>
          <IconButton onClick={() => setInvalidModalOpen(false)} aria-label="Close invalid files modal">
            <CloseIcon />
          </IconButton>
        </Box>
        <Box className="diagnostic-invalid-modal-body">
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Invalid files are blocked by format and filename rules.
          </Typography>
          <Box className="diagnostic-invalid-table">
            <Box className="diagnostic-modal-row diagnostic-modal-row--header">
              <Typography variant="caption" fontWeight={700}>
                File Name
              </Typography>
              <Typography variant="caption" fontWeight={700}>
                Reason
              </Typography>
            </Box>
            {invalidFiles.map((file) => (
              <Box key={`${file.name}-${file.reason}`} className="diagnostic-modal-row">
                <Typography variant="body2" className="diagnostic-modal-file-name">
                  {file.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {file.reason === "WHITESPACE_IN_FILENAME" ? "Whitespace in filename" : "File format not supported"}
                </Typography>
              </Box>
            ))}
            {invalidFiles.length === 0 && (
              <Box className="diagnostic-modal-empty-row">
                <Typography variant="body2" color="text.secondary">
                  No invalid files found.
                </Typography>
              </Box>
            )}
          </Box>
        </Box>
      </Dialog>
    </Dialog>
  );
}

export default DiagnosticModal;

