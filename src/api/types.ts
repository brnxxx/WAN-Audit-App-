export interface AdminOut {
  id: number;
  username: string;
  email: string | null;
  is_active: boolean;
  last_login: string | null;
}

export interface DeviceOut {
  id: number;
  name: string;
  hostname: string | null;
  ip_address: string | null;
  device_type: string;
  vendor: string | null;
  model: string | null;
  site_id: number | null;
  backbone_id: number | null;
  status: "online" | "offline" | "warning" | "unknown";
  management_protocol: string;
  username: string | null;
  port: number | null;
  site_name: string | null;
  backbone_name: string | null;
}

export interface GNS3Project {
  project_id: string;
  name: string;
  status: string;
}

export interface ImportResult {
  project: string;
  devices_created: number;
  devices_updated: number;
  links_created: number;
  links_updated: number;
  unmatched_site_warning: string[];
}
export interface GNS3Node {
  node_id: string;
  name: string;
  node_type: string;
  status?: string;
}
export interface GNS3Link {
  link_id: string;
  nodes: Array<{ node_id: string; label?: { text?: string } }>;
}
export interface GNS3Command {
  platform: string;
  category: string;
  command: string;
  purpose: string;
  risk: "read-only" | "state-changing";
}
export interface RouterCommandResult {
  project_id: string;
  source_node_id: string;
  source: string;
  command: string;
  output: string;
}
export interface PingResult {
  target: string;
  reachable: boolean;
  return_code: number;
  packets_sent: number;
  packets_received: number;
  packet_loss_percent: number;
  latency_min_ms: number | null;
  latency_avg_ms: number | null;
  latency_max_ms: number | null;
  output: string;
  source: string;
  execution: "server" | "gns3-node";
}
export interface TraceResult {
  target: string;
  reachable: boolean;
  return_code: number;
  hop_count: number;
  hops: Array<{ hop: number; detail: string }>;
  output: string;
  source: string;
  execution: "server" | "gns3-node";
}
export interface InfrastructureLog {
  id: number;
  project_id: string;
  event_type: "ping" | "traceroute" | "error" | string;
  status: "ok" | "issue" | "error" | string;
  source: string | null;
  target: string | null;
  message: string;
  details: string | null;
  created_at: string;
}
export interface SiteOut {
  id: number;
  name: string;
  description: string | null;
  location: string | null;
  created_at: string;
}

export interface BackboneOut {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
}

// Payload complet attendu par PUT /devices/{id} (le backend exige tous les champs)
export interface DeviceUpdatePayload {
  name: string;
  hostname: string | null;
  ip_address: string | null;
  device_type: string;
  vendor: string | null;
  model: string | null;
  site_id: number | null;
  backbone_id: number | null;
  management_protocol: string;
  username: string | null;
  port: number | null;
}