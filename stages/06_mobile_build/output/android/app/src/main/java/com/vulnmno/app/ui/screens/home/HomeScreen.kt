package com.vulnmno.app.ui.screens.home

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.MoreVert
import androidx.compose.material.icons.outlined.NotificationsNone
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.navigation.NavHostController
import com.vulnmno.app.data.remote.dto.BalanceDto
import com.vulnmno.app.data.remote.dto.CustomerDto
import com.vulnmno.app.data.remote.dto.PlanDto
import com.vulnmno.app.data.remote.dto.ProductDto
import com.vulnmno.app.data.repository.AccountsRepository
import com.vulnmno.app.data.repository.ApiResult
import com.vulnmno.app.data.repository.CustomerRepository
import com.vulnmno.app.data.repository.PlansRepository
import com.vulnmno.app.data.repository.ShopRepository
import com.vulnmno.app.ui.navigation.Routes
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.async
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class HomeUiState(
    val profile: CustomerDto? = null,
    val balance: BalanceDto? = null,
    val plan: PlanDto? = null,
    val offers: List<ProductDto> = emptyList(),
    val loading: Boolean = true,
    val error: String? = null,
)

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val customers: CustomerRepository,
    private val accounts: AccountsRepository,
    private val plans: PlansRepository,
    private val shop: ShopRepository,
) : ViewModel() {
    private val _state = MutableStateFlow(HomeUiState())
    val state: StateFlow<HomeUiState> = _state.asStateFlow()

    init { load() }

    fun load() = viewModelScope.launch {
        _state.update { it.copy(loading = true, error = null) }
        val me = async { customers.me() }
        val bal = async { accounts.balance() }
        val plan = async { plans.current() }
        val featured = async { shop.products(featured = true) }
        _state.update { st ->
            st.copy(
                profile = (me.await() as? ApiResult.Ok)?.value,
                balance = (bal.await() as? ApiResult.Ok)?.value,
                plan = (plan.await() as? ApiResult.Ok)?.value,
                offers = (featured.await() as? ApiResult.Ok)?.value?.items ?: emptyList(),
                loading = false,
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(nav: NavHostController, onLogout: () -> Unit, vm: HomeViewModel = hiltViewModel()) {
    val s by vm.state.collectAsState()
    var menu by remember { mutableStateOf(false) }
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("VulnMNO") },
                actions = {
                    IconButton(onClick = { nav.navigate(Routes.notifications) }) {
                        Icon(Icons.Outlined.NotificationsNone, contentDescription = "Notifications")
                    }
                    IconButton(onClick = { menu = true }) {
                        Icon(Icons.Outlined.MoreVert, contentDescription = "Menu")
                    }
                    DropdownMenu(expanded = menu, onDismissRequest = { menu = false }) {
                        DropdownMenuItem(text = { Text("Account") }, onClick = { menu = false; nav.navigate(Routes.account) })
                        DropdownMenuItem(text = { Text("Invoices") }, onClick = { menu = false; nav.navigate(Routes.invoices) })
                        DropdownMenuItem(text = { Text("Settings") }, onClick = { menu = false; nav.navigate(Routes.settings) })
                        DropdownMenuItem(text = { Text("Logout") }, onClick = { menu = false; onLogout() })
                    }
                }
            )
        }
    ) { pad ->
        Column(
            Modifier.padding(pad).padding(16.dp).fillMaxSize().verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            s.profile?.let { Text("Welcome, ${it.name}", style = MaterialTheme.typography.titleLarge) }
            ElevatedCard(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Text("Balance", style = MaterialTheme.typography.labelMedium)
                    Text(s.balance?.let { "${it.balance} ${it.currency}" } ?: "—",
                        style = MaterialTheme.typography.headlineSmall)
                    Spacer(Modifier.height(8.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedButton(onClick = { nav.navigate(Routes.balance) }) { Text("Details") }
                        FilledTonalButton(onClick = { nav.navigate(Routes.topup) }) { Text("Top up") }
                    }
                }
            }
            ElevatedCard(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp)) {
                    Text("Current plan", style = MaterialTheme.typography.labelMedium)
                    Text(s.plan?.name ?: "—", style = MaterialTheme.typography.titleMedium)
                    Spacer(Modifier.height(8.dp))
                    OutlinedButton(onClick = { nav.navigate(Routes.plans) }) { Text("Manage plan") }
                }
            }
            Text("Featured offers", style = MaterialTheme.typography.titleMedium)
            s.offers.forEach { p ->
                ElevatedCard(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        Text(p.name, style = MaterialTheme.typography.titleSmall)
                        Text("${p.price} ${p.currency}")
                        Spacer(Modifier.height(8.dp))
                        Button(onClick = { nav.navigate(Routes.product(p.productId)) }) { Text("View") }
                    }
                }
            }
            if (s.loading) LinearProgressIndicator(Modifier.fillMaxWidth())
        }
    }
}
