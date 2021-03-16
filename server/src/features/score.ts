import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import config from '../config.json';

export type FieldSideType = "blue" | "red";

export type TaskStateType = { [objectId: string]: number; };
export type ScoreStateType = {
  tasks: TaskStateType,   // タスクの進行状況
  enable: boolean,        // スコアの有効フラグ
  vgoal?: number,         // Vゴールタイム
};
export type WholeScoreState = Record<FieldSideType, ScoreStateType>;

type TaskUpdateActionPayload = {
  fieldSide: FieldSideType,
  taskObjectId: string,
  afterValue: number,
  // operation: string,     // バリデーションのために "increment"|"decrement" を指定する予定だったが現在使っていない
};

export const initialState: WholeScoreState = {
  blue: {
    tasks: Object.fromEntries(config.rule.task_objects.map(taskObj => [taskObj.id, taskObj.initialValue ?? 0])),
    enable: false,
    vgoal: undefined,
  },
  red: {
    tasks: Object.fromEntries(config.rule.task_objects.map(taskObj => [taskObj.id, taskObj.initialValue ?? 0])),
    enable: false,
    vgoal: undefined,
  },
};

export const scoreStateSlice = createSlice({
  name: 'task',
  initialState,
  reducers: {
    setTaskUpdate: (state, action: PayloadAction<TaskUpdateActionPayload>) => {
      state[action.payload.fieldSide].tasks[action.payload.taskObjectId] = action.payload.afterValue;
    },
    setScoreEnable: (state, action: PayloadAction<{fieldSide: FieldSideType, enable: boolean}>) => {
      state[action.payload.fieldSide].enable = action.payload.enable;
    },
    setVgoalTime: (state, action: PayloadAction<{fieldSide: FieldSideType, vgoalTime: number}>) => {
      state[action.payload.fieldSide].vgoal = action.payload.vgoalTime;
    },
    unsetVgoalTime: (state, action: PayloadAction<{fieldSide: FieldSideType}>) => {
      state[action.payload.fieldSide].vgoal = undefined;
    },
    setCurrent: (_, action: PayloadAction<WholeScoreState>) => action.payload,
  },
});
