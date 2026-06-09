import { useMemo, useState } from "react";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { SimpleTreeView } from "@mui/x-tree-view/SimpleTreeView";
import { TreeItem } from "@mui/x-tree-view/TreeItem";

const collectExpandableIds = (nodes) =>
  nodes.flatMap((node) => [
    ...(node.children?.length ? [node.id] : []),
    ...collectExpandableIds(node.children ?? []),
  ]);

function NodeLabel({ node }) {
  return (
    <Stack direction="row" alignItems="center" spacing={1} className="tree-label">
      <Typography component="span" variant="body2" fontWeight={node.type === "ticket" ? 500 : 700}>
        {node.label}
      </Typography>
      {node.type !== "ticket" && <Chip label={node.count} size="small" className="count-chip" />}
    </Stack>
  );
}

function renderNode(node, onTicketSelect, selectedTicketKey) {
  const isSelectedTicket = node.type === "ticket" && node.ticket?.key === selectedTicketKey;

  return (
    <TreeItem
      key={node.id}
      itemId={node.id}
      label={<NodeLabel node={node} />}
      className={isSelectedTicket ? "tree-item--selected" : undefined}
      onClick={() => {
        if (node.type === "ticket") {
          onTicketSelect(node.ticket);
        }
      }}
    >
      {(node.children ?? []).map((child) => renderNode(child, onTicketSelect, selectedTicketKey))}
    </TreeItem>
  );
}

function HierarchyTree({ nodes, onTicketSelect, selectedTicketKey }) {
  const expandableIds = useMemo(() => collectExpandableIds(nodes), [nodes]);
  const [expandedItems, setExpandedItems] = useState([]);

  return (
    <Stack spacing={2}>
      <Stack direction="row" spacing={1}>
        <Button size="small" variant="outlined" onClick={() => setExpandedItems(expandableIds)}>
          Expand All
        </Button>
        <Button size="small" variant="outlined" onClick={() => setExpandedItems([])}>
          Collapse All
        </Button>
      </Stack>
      {nodes.length === 0 ? (
        <Typography color="text.secondary">No tickets found for this filter.</Typography>
      ) : (
        <SimpleTreeView expandedItems={expandedItems} onExpandedItemsChange={(_, itemIds) => setExpandedItems(itemIds)}>
          {nodes.map((node) => renderNode(node, onTicketSelect, selectedTicketKey))}
        </SimpleTreeView>
      )}
    </Stack>
  );
}

export default HierarchyTree;
