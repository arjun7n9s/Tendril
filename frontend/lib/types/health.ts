// Source: backend/app/api/health.py

export type IntegrationFlag = "configured" | "not_configured";

export type HealthResponse = {
  status: "ok" | "error";
  database: "ok" | "error";
  bright_data_rest: IntegrationFlag;
  bright_data_browser: IntegrationFlag;
  bright_data_mcp: IntegrationFlag;
  aiml_api: IntegrationFlag;
  cognee: IntegrationFlag;
  triggerware: IntegrationFlag;
  speechmatics: IntegrationFlag;
  mock_mode: boolean;
  app_env: string;
};
