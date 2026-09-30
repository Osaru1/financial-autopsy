export type CategoryRow = {
  category: string;
  amount: string;
  delta: string | null;
};

export type SubscriptionItem = {
  merchant: string;
  monthly_amount: string;
  annual_amount: string;
  first_seen: string;
  last_seen: string;
  occurrences: number;
  total_spent: string;
  previous_amount: string | null;
  flags: string[];
};

export type AutopsyResponse = {
  empty: boolean;
  month: string;
  month_label: string;
  available_months: string[];
  income: string;
  spending: string;
  remaining: string;
  previous_label: string | null;
  spending_delta: string | null;
  narrative: string;
  categories: CategoryRow[];
  subscriptions: {
    count: number;
    monthly_cost: string;
    annual_cost: string;
    items: SubscriptionItem[];
    possible_new: SubscriptionItem[];
  };
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function requestAutopsy(path: string, init?: RequestInit): Promise<Response> {
  return fetch(`${API_URL}${path}`, { ...init, cache: "no-store" });
}

export async function readError(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
  } catch {
    return "The API sent back something unexpected.";
  }
  return "The API couldn't finish that request.";
}
