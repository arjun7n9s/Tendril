// Shared response shapes.
// Source: backend/app/schemas/common.py

export type Timestamped = {
  created_at: string;
  updated_at: string;
};

export type Paginated<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};
