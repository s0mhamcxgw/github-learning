CREATE TABLE `collector_state` (
	`key` text PRIMARY KEY NOT NULL,
	`value` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `documents` (
	`url` text PRIMARY KEY NOT NULL,
	`data` text NOT NULL,
	`collected_at` text NOT NULL
);
