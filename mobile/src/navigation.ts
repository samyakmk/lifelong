import type { NavigatorScreenParams } from "@react-navigation/native";

export type MemberTabs = { Home: undefined; Results: undefined };
export type RootStack = { Member: NavigatorScreenParams<MemberTabs> | undefined; Book: { orderId: number } };
