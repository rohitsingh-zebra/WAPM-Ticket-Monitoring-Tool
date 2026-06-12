import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Alert from "@mui/material/Alert";
import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Container from "@mui/material/Container";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Paper from "@mui/material/Paper";
import Select from "@mui/material/Select";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";

import { getCacheStatus, getHierarchy, getSummary, refreshCache, searchTickets } from "./api/client";
import HierarchyTree from "./components/HierarchyTree";
import MetricCard from "./components/MetricCard";
import TicketDetailsPanel from "./components/TicketDetailsPanel";

const formatTime = (value) => {
  if (!value) {
    return "-";
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
};

function App() {
  const [days, setDays] = useState(2);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTicket, setSelectedTicket] = useState(null);
  const queryClient = useQueryClient();

  const summaryQuery = useQuery({
    queryKey: ["summary", days],
    queryFn: () => getSummary(days),
  });

  const hierarchyQuery = useQuery({
    queryKey: ["hierarchy", days],
    queryFn: () => getHierarchy(days),
  });

  const statusQuery = useQuery({
    queryKey: ["cache-status"],
    queryFn: getCacheStatus,
    refetchInterval: 60_000,
  });

  const searchQueryResult = useQuery({
    queryKey: ["search", searchQuery],
    queryFn: () => searchTickets(searchQuery),
    enabled: searchQuery.trim().length > 0,
  });

  const refreshMutation = useMutation({
    mutationFn: refreshCache,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["summary"] });
      queryClient.invalidateQueries({ queryKey: ["hierarchy"] });
      queryClient.invalidateQueries({ queryKey: ["cache-status"] });
      queryClient.invalidateQueries({ queryKey: ["search"] });
    },
  });

  const metrics = useMemo(() => {
    const summary = summaryQuery.data;
    return [
      ["Total Tickets", summary?.total_tickets],
      ["To Do", summary?.open_tickets],
      ["In Progress", summary?.in_progress_tickets],
      ["Resolved", summary?.resolved_tickets],
      ["Issue Categories", summary?.total_categories],
      ["Last Refresh", formatTime(summary?.last_refresh_time)],
    ];
  }, [summaryQuery.data]);

  const isLoading = summaryQuery.isLoading || hierarchyQuery.isLoading;
  const error = summaryQuery.error || hierarchyQuery.error || statusQuery.error || refreshMutation.error;
  const searchResults = searchQuery.trim() ? searchQueryResult.data?.tickets ?? [] : [];

  return (
    <>
      <AppBar position="static" elevation={0} className="top-bar">
        <Toolbar className="top-toolbar">
          <Box>
            <Typography variant="h6" component="h1" fontWeight={800}>
              WAPM Ticket Monitoring Dashboard
            </Typography>
            <Typography variant="body2" className="top-subtitle">
              Workforce AppMonitoring | Jira operational visibility
            </Typography>
          </Box>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Stack spacing={3}>
          <Paper elevation={0} className="control-panel">
            <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ alignItems: { md: "center" } }}>
              <FormControl sx={{ minWidth: 180 }}>
                <InputLabel id="days-filter-label">Date Filter</InputLabel>
                <Select
                  labelId="days-filter-label"
                  value={days}
                  label="Date Filter"
                  onChange={(event) => setDays(Number(event.target.value))}
                >
                  <MenuItem value={2}>Last 2 Days</MenuItem>
                  <MenuItem value={7}>Last 7 Days</MenuItem>
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Search ticket ID, issue category, cluster_id, clientId Env, or summary"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
              />

              <Button
                variant="contained"
                disabled={refreshMutation.isPending}
                onClick={() => refreshMutation.mutate()}
                sx={{ minWidth: 150 }}
              >
                {refreshMutation.isPending ? "Refreshing..." : "Refresh"}
              </Button>
            </Stack>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Cache status: {statusQuery.data?.cache_health_status ?? "unknown"} | Last refresh:{" "}
              {formatTime(statusQuery.data?.last_refresh_time)}
            </Typography>
          </Paper>

          {error && (
            <Alert severity="error">
              {error.response?.data?.detail ?? error.message ?? "Unable to load dashboard data."}
            </Alert>
          )}

          <Box className="metrics-grid">
            {metrics.map(([label, value]) => (
              <MetricCard label={label} value={value} key={label} />
            ))}
          </Box>

          {isLoading ? (
            <Box className="loading-box">
              <CircularProgress />
            </Box>
          ) : (
            <Box className={`content-area ${selectedTicket ? "content-area--details-open" : ""}`}>
              <Paper elevation={0} className="dashboard-panel hierarchy-panel">
                <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} sx={{ mb: 2, justifyContent: "space-between" }}>
                  <Box>
                    <Typography variant="h6" fontWeight={800}>
                      Tickets by Issue Category
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Grouped dynamically from ticket issue names
                    </Typography>
                  </Box>
                  <Chip label={`${days} day view`} className="panel-chip" />
                </Stack>
                  {searchQuery.trim() ? (
                    <Stack spacing={1.25}>
                      <Typography color="text.secondary">
                        {searchQueryResult.isFetching ? "Searching..." : `${searchResults.length} result(s)`}
                      </Typography>
                      {searchResults.map((ticket) => (
                        <Button
                          key={ticket.key}
                          variant="outlined"
                          color="inherit"
                          className={`search-result ${selectedTicket?.key === ticket.key ? "search-result--selected" : ""}`}
                          onClick={() => setSelectedTicket(ticket)}
                        >
                          <Box textAlign="left" width="100%">
                            <Typography fontWeight={700}>{ticket.key}</Typography>
                            <Typography variant="body2" color="text.secondary">
                              {ticket.category} | {ticket.cluster} / {ticket.organization}
                            </Typography>
                            <Typography variant="body2">{ticket.summary}</Typography>
                          </Box>
                        </Button>
                      ))}
                    </Stack>
                  ) : (
                    <HierarchyTree
                      nodes={hierarchyQuery.data?.data ?? []}
                      onTicketSelect={setSelectedTicket}
                      selectedTicketKey={selectedTicket?.key}
                    />
                  )}
              </Paper>

              <TicketDetailsPanel
                ticket={selectedTicket}
                open={Boolean(selectedTicket)}
                onClose={() => setSelectedTicket(null)}
              />
            </Box>
          )}
        </Stack>
      </Container>
    </>
  );
}

export default App;
