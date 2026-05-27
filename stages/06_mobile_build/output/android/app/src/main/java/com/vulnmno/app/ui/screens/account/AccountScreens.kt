package com.vulnmno.app.ui.screens.account

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.navigation.NavHostController
import com.vulnmno.app.data.remote.dto.*
import com.vulnmno.app.data.repository.*
import com.vulnmno.app.ui.navigation.Routes
import com.vulnmno.app.ui.screens.ErrorBox
import com.vulnmno.app.ui.screens.LoadingBox
import com.vulnmno.app.ui.screens.retryable
import com.vulnmno.app.ui.screens.userMessage
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.async
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

// ---------- Account ----------

@HiltViewModel
class AccountViewModel @Inject constructor(
    private val customers: CustomerRepository,
    private val loyalty: LoyaltyRepository,
) : ViewModel() {
    sealed interface S {
        data object Loading : S
        data class Loaded(
            val customer: CustomerDto,
            val lines: List<MobileLineDto>,
            val loyaltyAccount: LoyaltyAccountDto? = null,
        ) : S
        data class Err(val msg: String, val retry: Boolean) : S
    }
    private val _s = MutableStateFlow<S>(S.Loading)
    val s: StateFlow<S> = _s.asStateFlow()
    init { load() }
    fun load() = viewModelScope.launch {
        _s.value = S.Loading
        // Fan-out three parallel reads. Loyalty is best-effort: a 4xx from it should not
        // block the whole AccountScreen.
        val meDeferred = async { customers.me() }
        val linesDeferred = async { customers.lines() }
        val loyaltyDeferred = async { loyalty.account() }
        val me = meDeferred.await()
        val lines = linesDeferred.await()
        val loy = loyaltyDeferred.await()
        _s.value = when {
            me is ApiResult.Ok && lines is ApiResult.Ok -> S.Loaded(
                me.value,
                lines.value.items,
                (loy as? ApiResult.Ok)?.value,
            )
            me is ApiResult.Err -> S.Err(me.error.userMessage(), me.error.retryable())
            lines is ApiResult.Err -> S.Err(lines.error.userMessage(), lines.error.retryable())
            else -> S.Err("Unexpected error", true)
        }
    }
}

@Composable
fun AccountScreen(nav: NavHostController, vm: AccountViewModel = hiltViewModel()) {
    when (val s = vm.s.collectAsState().value) {
        AccountViewModel.S.Loading -> LoadingBox()
        is AccountViewModel.S.Err -> ErrorBox(s.msg, s.retry, vm::load)
        is AccountViewModel.S.Loaded -> Column(
            Modifier.padding(16.dp).fillMaxSize().verticalScroll(rememberScrollState())
        ) {
            Text(s.customer.name, style = MaterialTheme.typography.titleLarge)
            Text(s.customer.primaryMsisdn)
            s.customer.email?.let { Text(it) }
            Text("Plan type: ${s.customer.accountType} / Tier: ${s.customer.loyaltyTier}")
            Spacer(Modifier.height(16.dp))
            Text("Lines", style = MaterialTheme.typography.titleMedium)
            s.lines.forEach { Text("• ${it.msisdn} (${it.status})") }

            // ---- Loyalty section (Phase 2) ----
            s.loyaltyAccount?.let { la ->
                Spacer(Modifier.height(16.dp))
                ElevatedCard(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp)) {
                        Text("Loyalty", style = MaterialTheme.typography.titleMedium)
                        Spacer(Modifier.height(4.dp))
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Column {
                                Text("Points", style = MaterialTheme.typography.labelMedium)
                                Text(
                                    "${la.points}",
                                    style = MaterialTheme.typography.headlineSmall,
                                )
                            }
                            Column(horizontalAlignment = androidx.compose.ui.Alignment.End) {
                                Text("Tier", style = MaterialTheme.typography.labelMedium)
                                Text(
                                    la.tier.replaceFirstChar { it.titlecase() },
                                    style = MaterialTheme.typography.headlineSmall,
                                )
                            }
                        }
                        Text(
                            "× ${la.multiplier} points / EUR · lifetime ${la.lifetimePoints}",
                            style = MaterialTheme.typography.bodySmall,
                        )
                        if (la.nextTier != null && la.pointsToNextTier != null) {
                            Spacer(Modifier.height(8.dp))
                            Text(
                                "${la.pointsToNextTier} pts to ${la.nextTier}",
                                style = MaterialTheme.typography.bodySmall,
                            )
                        }
                    }
                }
            }

            Spacer(Modifier.height(16.dp))
            FilledTonalButton(onClick = { nav.navigate(Routes.sim) }) { Text("View SIM profile") }
            Spacer(Modifier.height(8.dp))
            OutlinedButton(onClick = { nav.navigate(Routes.settings) }) { Text("Settings") }
        }
    }
}

// ---------- SIM ----------

@HiltViewModel
class SimViewModel @Inject constructor(private val customers: CustomerRepository) : ViewModel() {
    sealed interface S { data object Loading : S; data class Loaded(val sim: SimProfileDto) : S; data class Err(val msg: String) : S }
    private val _s = MutableStateFlow<S>(S.Loading); val s: StateFlow<S> = _s.asStateFlow()
    init { viewModelScope.launch {
        _s.value = when (val r = customers.sim()) {
            is ApiResult.Ok -> S.Loaded(r.value); is ApiResult.Err -> S.Err(r.error.userMessage())
        }
    } }
}

@Composable
fun SimProfileScreen(vm: SimViewModel = hiltViewModel()) {
    when (val s = vm.s.collectAsState().value) {
        SimViewModel.S.Loading -> LoadingBox()
        is SimViewModel.S.Err -> ErrorBox(s.msg)
        is SimViewModel.S.Loaded -> Column(Modifier.padding(16.dp)) {
            Text("SIM profile", style = MaterialTheme.typography.titleLarge)
            Text("SIM ID: ${s.sim.simId}")
            Text("ICCID: ${s.sim.iccid}")
            Text("Type: ${s.sim.type}")
            Text("Status: ${s.sim.status}")
            Text("Activated: ${s.sim.activationDate}")
        }
    }
}

// ---------- Notifications ----------

@HiltViewModel
class NotificationsViewModel @Inject constructor(private val repo: NotificationsRepository) : ViewModel() {
    data class S(val items: List<NotificationDto> = emptyList(), val loading: Boolean = true, val err: String? = null)
    private val _s = MutableStateFlow(S()); val s: StateFlow<S> = _s.asStateFlow()
    init { load() }
    fun load() = viewModelScope.launch {
        _s.update { it.copy(loading = true, err = null) }
        when (val r = repo.list()) {
            is ApiResult.Ok -> _s.value = S(items = r.value.items, loading = false)
            is ApiResult.Err -> _s.value = S(loading = false, err = r.error.userMessage())
        }
    }
}

@Composable
fun NotificationsScreen(vm: NotificationsViewModel = hiltViewModel()) {
    val s = vm.s.collectAsState().value
    if (s.loading) LoadingBox()
    else if (s.err != null) ErrorBox(s.err, true, vm::load)
    else LazyColumn(Modifier.fillMaxSize().padding(16.dp)) {
        items(s.items) { n ->
            ElevatedCard(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                Column(Modifier.padding(16.dp)) {
                    Text(n.title, style = MaterialTheme.typography.titleSmall)
                    Text(n.body)
                    Text("${n.channel} • ${n.createdAt}", style = MaterialTheme.typography.labelSmall)
                }
            }
        }
    }
}
