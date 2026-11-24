import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { DefaultTheme, NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";

import type { MemberTabs, RootStack } from "./src/navigation";
import { Book } from "./src/screens/Book";
import { Home } from "./src/screens/Home";
import { Results } from "./src/screens/Results";
import { SignIn } from "./src/screens/SignIn";
import { SessionProvider, useSession } from "./src/session";
import { color, Icon, Loading, styles } from "./src/ui";

const Stack = createNativeStackNavigator<RootStack>();
const Tab = createBottomTabNavigator<MemberTabs>();
const theme = {
    ...DefaultTheme,
    colors: {
        ...DefaultTheme.colors,
        background: color.canvas,
        card: color.canvas,
        border: color.line,
        primary: color.forest,
        text: color.ink,
    },
};

function Tabs() {
    return (
        <Tab.Navigator
            screenOptions={({ route }) => ({
                headerShown: false,
                tabBarActiveTintColor: color.forest,
                tabBarInactiveTintColor: color.muted,
                tabBarHideOnKeyboard: true,
                tabBarLabelStyle: { fontSize: 12, fontWeight: "700" },
                tabBarStyle: { backgroundColor: color.surface, borderTopColor: color.line },
                tabBarIcon: ({ focused, color: tint }) => <Icon
                    name={route.name === "Home" ? (focused ? "house.fill" : "house") : "chart.line.uptrend.xyaxis"}
                    size={22}
                    tint={tint}
                />,
            })}
        >
            <Tab.Screen name="Home" component={Home} />
            <Tab.Screen name="Results" component={Results} />
        </Tab.Navigator>
    );
}

function MemberApp() {
    const { token, restoring } = useSession();
    if (restoring) {
        return (
            <SafeAreaView style={[styles.screen, { justifyContent: "center" }]}>
                <Loading label="Opening Baseline…" />
            </SafeAreaView>
        );
    }
    if (!token) {
        return <SignIn />;
    }
    return (
        <NavigationContainer theme={theme}>
            <Stack.Navigator screenOptions={{ headerTintColor: color.forest, headerShadowVisible: false, contentStyle: styles.screen }}>
                <Stack.Screen name="Member" component={Tabs} options={{ headerShown: false }} />
                <Stack.Screen name="Book" component={Book} options={{ title: "Book a draw", headerBackButtonDisplayMode: "minimal" }} />
            </Stack.Navigator>
        </NavigationContainer>
    );
}

export default function App() {
    return (
        <SafeAreaProvider>
            <StatusBar style="dark" />
            <SessionProvider>
                <MemberApp />
            </SessionProvider>
        </SafeAreaProvider>
    );
}
