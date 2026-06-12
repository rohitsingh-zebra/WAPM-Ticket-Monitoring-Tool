import { useState } from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Link from "@mui/material/Link";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import DiagnosticModal from "./DiagnosticModal";

const formatDate = (value) => {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
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
  const [isDiagnosticModalOpen, setDiagnosticModalOpen] = useState(false);

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
        <Button variant="contained" onClick={() => setDiagnosticModalOpen(true)}>
          Run
        </Button>
      </Box>
      <DiagnosticModal ticket={ticket} open={isDiagnosticModalOpen} onClose={() => setDiagnosticModalOpen(false)} />
    </Stack>
  );
}

export default TicketDetails;
