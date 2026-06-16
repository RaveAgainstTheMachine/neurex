// src/lib/store.ts
import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import { subscribeWithSelector } from "zustand/middleware";
import type { NeurexStore } from "./types";

import { createSystemSlice } from './stores/systemSlice';
import { createAuthSlice } from './stores/authSlice';
import { createInfraSlice } from './stores/infraSlice';
import { createFiletreeSlice } from './stores/fileTreeSlice';
import { createChatSlice } from './stores/chatSlice';
import { createTaskSlice } from './stores/taskSlice';
import { createEditorSlice } from './stores/editorSlice';

export const useStore = create<NeurexStore>()(
  subscribeWithSelector(
    immer((...a) => ({
      ...createSystemSlice(...a),
      ...createAuthSlice(...a),
      ...createInfraSlice(...a),
      ...createFiletreeSlice(...a),
      ...createChatSlice(...a),
      ...createTaskSlice(...a),
      ...createEditorSlice(...a),
    }))
  )
);
