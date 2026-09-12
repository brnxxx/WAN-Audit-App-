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