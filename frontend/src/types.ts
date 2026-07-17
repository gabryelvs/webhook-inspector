export interface Bin {
  id: string;
  name: string | null;
  created_at: string;
}

export interface CapturedRequest {
  id: string;
  bin_id: string;
  method: string;
  path: string;
  headers: Record<string, string>;
  query: Record<string, string>;
  body: string;
  content_type: string | null;
  source_ip: string | null;
  truncated: boolean;
  received_at: string;
}
