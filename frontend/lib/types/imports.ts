// Source: backend/app/schemas/import_seed.py

export type SeedImportResponse = {
  import_id: string;
  accounts_created: number;
  accounts_updated: number;
  people_created: number;
  people_updated: number;
  icp_profiles_created: number;
  icp_profiles_updated: number;
  warnings: string[];
};
