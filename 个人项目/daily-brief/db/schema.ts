// Intentionally empty by default.
// Add Drizzle tables here when the site actually needs a database.
// See examples/d1/db/schema.ts for an opt-in example.
import { sqliteTable, text } from "drizzle-orm/sqlite-core";

export const documents = sqliteTable("documents", {
  url: text("url").primaryKey(),
  data: text("data").notNull(),
  collectedAt: text("collected_at").notNull(),
});
export const collectorState = sqliteTable("collector_state", {
  key: text("key").primaryKey(),
  value: text("value").notNull(),
});
