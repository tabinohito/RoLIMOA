import { z } from "zod";

const vgoalConditionSchema = z.union([
  z.object({
    type: z.literal("manual"),
    required: z.object({
      tasks: z.array(
        z.object({
          id: z.string(),
          count: z.number(),
        }),
      ),
    }),
  }),
  z.object({
    type: z.literal("alwaysOk"),
  }),
]);

const timeProgressSchema = z.object({
  id: z.string(),
  type: z.enum(["default", "ready", "count"]),
  time: z.number().optional(),
  description: z.string(),
  isAutoTransition: z.boolean().optional(),
  style: z.object({
    timerFormat: z.enum(["mm:ss", "m:ss", "ss", "s"]).optional(),
    timerType: z.string().optional(),
  }).optional(),
  custom: z.array(
    z.object({
      elapsedTime: z.number(),
      displayText: z.string().optional(),
      sound: z.string().optional(),
    }),
  ).optional(),
});

export const configSchema = z.object({
  contest_info: z.object({
    name: z.string(),
  }),
  rule: z.object({
    task_objects: z.array(
      z.object({
        id: z.string(),
        description: z.string(),
        initialValue: z.number().optional(),
        min: z.number().optional(),
        max: z.number().optional(),
      }),
    ),
    score: z.union([
      z.object({
        format: z.literal("simple"),
        expression: z.array(
          z.object({
            id: z.string(),
            coefficient: z.number(),
          }),
        ),
      }),
      z.object({
        format: z.literal("formulaExpression"),
        expression: z.any(), // 再帰構造を含むのでとりあえずany
      }),
    ]),
    vgoal: z.object({
      name: z.string(),
      condition: vgoalConditionSchema,
    }),
  }),
  time_progress: z.array(
    timeProgressSchema
  ),
  teams_info: z.array(
    z.object({
      id: z.string(),
      name: z.string(),
      school: z.string(),
      short: z.string(),
    }),
  ),
  client: z.object({
    standalone_mode: z.boolean(),
  }),
});
