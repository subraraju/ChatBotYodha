/* ── Types shared across the frontend ────────────────────────────── */

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface SessionInfo {
  session_id: string;
  customer_state: string;
  customer_id?: number;
  customer_info: Record<string, unknown>;
  recent_purchases: Purchase[];
  selected_product?: Purchase;
  messages: Message[];
  debug_info?: Record<string, unknown>;
}

export interface Purchase {
  sale_id: number;
  product_id: number;
  product_name: string;
  category: string;
  type: string;
  version: string;
  price: number;
  quantity: number;
  sale_date: string;
  total_amount: number;
}

export interface StartSessionResponse {
  session_id: string;
  welcome_message: string;
}

export interface MessageResponse {
  response: string;
  session: SessionInfo;
}

export interface ConfigResponse {
  company_name: string;
  llm_provider: string;
  embedding_model: string;
  storage_backend: string;
}
