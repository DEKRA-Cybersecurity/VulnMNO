package com.vulnmno.app.ui.navigation

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Layers
import androidx.compose.material.icons.outlined.LocalMall
import androidx.compose.material.icons.outlined.QueryStats
import androidx.compose.material.icons.outlined.SupportAgent
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.navArgument
import androidx.navigation.navDeepLink
import androidx.compose.material.icons.outlined.Home
import com.vulnmno.app.ui.screens.account.AccountScreen
import com.vulnmno.app.ui.screens.account.NotificationsScreen
import com.vulnmno.app.ui.screens.account.SimProfileScreen
import com.vulnmno.app.ui.screens.auth.LoginScreen
import com.vulnmno.app.ui.screens.auth.OtpScreen
import com.vulnmno.app.ui.screens.auth.PasswordResetConfirmScreen
import com.vulnmno.app.ui.screens.auth.PasswordResetRequestScreen
import com.vulnmno.app.ui.screens.auth.SplashScreen
import com.vulnmno.app.ui.screens.balance.BalanceScreen
import com.vulnmno.app.ui.screens.balance.TopUpScreen
import com.vulnmno.app.ui.screens.balance.TransactionsScreen
import com.vulnmno.app.ui.screens.home.HomeScreen
import com.vulnmno.app.ui.screens.invoices.InvoiceDetailScreen
import com.vulnmno.app.ui.screens.invoices.InvoicesScreen
import com.vulnmno.app.ui.screens.invoices.RefundRequestScreen
import com.vulnmno.app.ui.screens.plans.PlanChangeScreen
import com.vulnmno.app.ui.screens.plans.PlansScreen
import com.vulnmno.app.ui.screens.settings.SettingsScreen
import com.vulnmno.app.ui.screens.shop.CheckoutScreen
import com.vulnmno.app.ui.screens.shop.ProductDetailScreen
import com.vulnmno.app.ui.screens.shop.PurchaseConfirmationScreen
import com.vulnmno.app.ui.screens.shop.ShopScreen
import com.vulnmno.app.ui.screens.support.NewTicketScreen
import com.vulnmno.app.ui.screens.support.SupportTicketsScreen
import com.vulnmno.app.ui.screens.support.TicketDetailScreen
import com.vulnmno.app.ui.screens.usage.UsageScreen

private data class TopTab(val route: String, val label: String, val icon: androidx.compose.ui.graphics.vector.ImageVector)

private val tabs = listOf(
    TopTab(Routes.home, "Home", Icons.Outlined.Home),
    TopTab(Routes.shop, "Shop", Icons.Outlined.LocalMall),
    TopTab(Routes.plans, "Plans", Icons.Outlined.Layers),
    TopTab(Routes.usage, "Usage", Icons.Outlined.QueryStats),
    TopTab(Routes.support, "Support", Icons.Outlined.SupportAgent),
)

@Composable
fun VulnMnoNavHost(
    nav: NavHostController,
    authState: AuthState,
    onAuthEvent: (AuthIntent) -> Unit,
) {
    val backStack by nav.currentBackStackEntryAsState()
    val currentRoute = backStack?.destination?.route
    val onTopTab = currentRoute in tabs.map { it.route }

    LaunchedEffect(authState) {
        when (authState) {
            AuthState.LoggedIn -> if (currentRoute == null || currentRoute == Routes.splash || currentRoute == Routes.login) {
                nav.navigate(Routes.home) { popUpTo(0) }
            }
            AuthState.LoggedOut -> if (currentRoute != Routes.login) {
                // Includes the bootstrap case: from splash, AuthGate resolves with no tokens
                // and we need to advance to login. The previous condition skipped splash and
                // left the user stuck on the loading spinner forever.
                nav.navigate(Routes.login) { popUpTo(0) }
            }
            AuthState.Resolving -> Unit
        }
    }

    Scaffold(
        bottomBar = {
            if (onTopTab) {
                NavigationBar {
                    tabs.forEach { t ->
                        NavigationBarItem(
                            selected = currentRoute == t.route,
                            onClick = {
                                nav.navigate(t.route) {
                                    popUpTo(nav.graph.findStartDestination().id) { saveState = true }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            },
                            icon = { Icon(t.icon, contentDescription = t.label) },
                            label = { Text(t.label) },
                        )
                    }
                }
            }
        }
    ) { padding ->
        NavHost(
            navController = nav,
            startDestination = Routes.splash,
            modifier = Modifier.padding(padding),
        ) {
            composable(Routes.splash) { SplashScreen() }
            composable(Routes.login) { LoginScreen(nav) }
            composable(
                Routes.otp,
                arguments = listOf(navArgument("challengeToken") { type = NavType.StringType }),
            ) { entry ->
                OtpScreen(nav, entry.arguments?.getString("challengeToken").orEmpty())
            }
            composable(Routes.pwResetRequest) { PasswordResetRequestScreen(nav) }
            composable(Routes.pwResetConfirm,
                arguments = listOf(navArgument("msisdn") { type = NavType.StringType })) { entry ->
                PasswordResetConfirmScreen(nav, entry.arguments?.getString("msisdn").orEmpty())
            }

            composable(Routes.home, deepLinks = listOf(navDeepLink { uriPattern = "vulnmno://home" })) {
                HomeScreen(nav, onLogout = { onAuthEvent(AuthIntent.Logout) })
            }
            composable(Routes.shop, deepLinks = listOf(navDeepLink { uriPattern = "vulnmno://shop" })) {
                ShopScreen(nav)
            }
            composable(Routes.plans) { PlansScreen(nav) }
            composable(Routes.usage) { UsageScreen() }
            composable(Routes.support) { SupportTicketsScreen(nav) }

            composable(Routes.account) { AccountScreen(nav) }
            composable(Routes.settings) { SettingsScreen(nav) }
            composable(Routes.sim) { SimProfileScreen() }
            composable(Routes.balance) { BalanceScreen(nav) }
            composable(Routes.topup) { TopUpScreen(nav) }
            composable(Routes.transactions) { TransactionsScreen() }
            composable(Routes.invoices) { InvoicesScreen(nav) }
            composable(Routes.invoice,
                arguments = listOf(navArgument("invoiceId") { type = NavType.StringType }),
                deepLinks = listOf(navDeepLink { uriPattern = "vulnmno://invoice/{invoiceId}" })) { entry ->
                InvoiceDetailScreen(nav, entry.arguments?.getString("invoiceId").orEmpty())
            }
            composable(Routes.refund,
                arguments = listOf(
                    navArgument("targetType") { type = NavType.StringType },
                    navArgument("targetId") { type = NavType.StringType },
                )) { entry ->
                RefundRequestScreen(
                    nav,
                    entry.arguments?.getString("targetType").orEmpty(),
                    entry.arguments?.getString("targetId").orEmpty(),
                )
            }
            composable(Routes.notifications,
                deepLinks = listOf(navDeepLink { uriPattern = "vulnmno://notifications" })) { NotificationsScreen() }

            composable(Routes.product,
                arguments = listOf(navArgument("productId") { type = NavType.StringType }),
                deepLinks = listOf(navDeepLink { uriPattern = "vulnmno://product/{productId}" })) { entry ->
                ProductDetailScreen(nav, entry.arguments?.getString("productId").orEmpty())
            }
            composable(Routes.checkout,
                arguments = listOf(navArgument("productId") { type = NavType.StringType })) { entry ->
                CheckoutScreen(nav, entry.arguments?.getString("productId").orEmpty())
            }
            composable(Routes.purchaseConfirmation,
                arguments = listOf(navArgument("purchaseId") { type = NavType.StringType })) { entry ->
                PurchaseConfirmationScreen(nav, entry.arguments?.getString("purchaseId").orEmpty())
            }

            composable(Routes.planChange,
                arguments = listOf(navArgument("planId") { type = NavType.StringType })) { entry ->
                PlanChangeScreen(nav, entry.arguments?.getString("planId").orEmpty())
            }

            composable(Routes.supportNew,
                arguments = listOf(navArgument("topic") {
                    type = NavType.StringType; nullable = true; defaultValue = null
                })) { entry ->
                NewTicketScreen(nav, entry.arguments?.getString("topic"))
            }
            composable(Routes.ticket,
                arguments = listOf(navArgument("ticketId") { type = NavType.StringType }),
                deepLinks = listOf(navDeepLink { uriPattern = "vulnmno://support/ticket/{ticketId}" })) { entry ->
                TicketDetailScreen(nav, entry.arguments?.getString("ticketId").orEmpty())
            }
        }
    }
}
