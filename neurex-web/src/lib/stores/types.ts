import { StateCreator } from "zustand";
import { NeurexStore } from "../types";

export type StoreSlice<T> = StateCreator<
  NeurexStore,
  [["zustand/immer", never], ["zustand/subscribeWithSelector", never]],
  [],
  T
>;
