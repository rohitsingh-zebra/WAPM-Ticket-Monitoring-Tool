import CloseIcon from "@mui/icons-material/Close";
import Box from "@mui/material/Box";
import IconButton from "@mui/material/IconButton";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import TicketDetails from "./TicketDetails";

function TicketDetailsPanel({ ticket, open, onClose }) {
  return (
    <>
      <Box
        className={`details-backdrop ${open ? "details-backdrop--visible" : ""}`}
        onClick={onClose}
        aria-hidden={!open}
      />
      <Paper
        elevation={0}
        className={`dashboard-panel details-drawer ${open ? "details-drawer--open" : ""}`}
        aria-hidden={!open}
      >
        <Stack direction="row" sx={{ mb: 2, justifyContent: "space-between", alignItems: "center" }}>
          <Typography variant="h6" fontWeight={800}>
            Ticket Details
          </Typography>
          <IconButton aria-label="Close ticket details" onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Stack>
        <TicketDetails ticket={ticket} />
      </Paper>
    </>
  );
}

export default TicketDetailsPanel;
