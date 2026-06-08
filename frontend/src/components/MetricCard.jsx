import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

function MetricCard({ label, value }) {
  return (
    <Card elevation={0} className="metric-card">
      <CardContent>
        <Box className="metric-accent" />
        <Typography variant="overline" color="text.secondary" className="metric-label">
          {label}
        </Typography>
        <Typography variant="h4" fontWeight={800} className="metric-value">
          {value ?? "-"}
        </Typography>
      </CardContent>
    </Card>
  );
}

export default MetricCard;
