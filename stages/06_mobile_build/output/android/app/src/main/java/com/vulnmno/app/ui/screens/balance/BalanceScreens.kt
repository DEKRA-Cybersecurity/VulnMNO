package com.vulnmno.app.ui.screens.balance

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.navigation.NavHostController
import com.vulnmno.app.data.remote.dto.BalanceDto
import com.vulnmno.app.data.remote.dto.TransactionDto
import com.vulnmno.app.data.repository.AccountsRepository
import com.vulnmno.app.data.repository.ApiResult
import com.vulnmno.app.ui.navigation.Routes
import com.vulnmno.app.ui.screens.ErrorBox
import com.vulnmno.app.ui.screens.LoadingBox
import com.vulnmno.app.ui.screens.OnResume
import com.vulnmno.app.ui.screens.userMessage
import dagger.hilt.android.lifecycle.HiltViewModel
import java.math.BigDecimal
import java.util.UUID
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

@HiltViewModel
class BalanceViewModel @Inject constructor(private val repo: AccountsRepository) : ViewModel() {
    sealed interface S { data object Loading : S; data class Loaded(val b: BalanceDto) : S; data class Err(val msg: String) : S }
    private val _s = MutableStateFlow<S>(S.Loading); val s: StateFlow<S> = _s.asStateFlow()
    fun load() = viewModelScope.launch {
        _s.value = S.Loading
        _s.value = when (val r = repo.balance()) {
            is ApiResult.Ok -> S.Loaded(r.value); is ApiResult.Err -> S.Err(r.error.userMessage())
        }
    }
}

@Composable
fun BalanceScreen(nav: NavHostController, vm: BalanceViewModel = hiltViewModel()) {
    OnResume { vm.load() }   // refresh after TopUp/Purchase/etc. pops back here
    when (val s = vm.s.collectAsState().value) {
        BalanceViewModel.S.Loading -> LoadingBox()
        is BalanceViewModel.S.Err -> ErrorBox(s.msg, true, vm::load)
        is BalanceViewModel.S.Loaded -> Column(Modifier.fillMaxSize().padding(16.dp)) {
            Text("Current balance", style = MaterialTheme.typography.titleMedium)
            Text("${s.b.balance} ${s.b.currency}", style = MaterialTheme.typography.headlineMedium)
            Text("Updated ${s.b.lastUpdated}", style = MaterialTheme.typography.labelSmall)
            Spacer(Modifier.height(16.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilledTonalButton(onClick = { nav.navigate(Routes.topup) }) { Text("Top up") }
                OutlinedButton(onClick = { nav.navigate(Routes.transactions) }) { Text("Transactions") }
            }
        }
    }
}

@HiltViewModel
class TopUpViewModel @Inject constructor(private val repo: AccountsRepository) : ViewModel() {
    data class S(val submitting: Boolean = false, val amountError: String? = null, val success: Boolean = false)
    private val _s = MutableStateFlow(S()); val s: StateFlow<S> = _s.asStateFlow()
    fun submit(amount: String, idempotencyKey: String) = viewModelScope.launch {
        val parsed = try { BigDecimal(amount) } catch (_: Throwable) {
            _s.value = S(amountError = "Invalid amount"); return@launch
        }
        _s.value = S(submitting = true)
        _s.value = when (val r = repo.topUp(idempotencyKey, parsed)) {
            is ApiResult.Ok -> S(success = true)
            is ApiResult.Err -> S(amountError = r.error.userMessage())
        }
    }
}

@Composable
fun TopUpScreen(nav: NavHostController, vm: TopUpViewModel = hiltViewModel()) {
    var amount by rememberSaveable { mutableStateOf("10.00") }
    val key = rememberSaveable { UUID.randomUUID().toString() }
    val s = vm.s.collectAsState().value
    LaunchedEffect(s.success) { if (s.success) nav.popBackStack() }
    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Text("Top up wallet", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(16.dp))
        OutlinedTextField(value = amount, onValueChange = { amount = it }, label = { Text("Amount (EUR)") }, keyboardOptions = androidx.compose.foundation.text.KeyboardOptions(keyboardType = KeyboardType.Decimal), modifier = Modifier.fillMaxWidth())
        s.amountError?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        Spacer(Modifier.height(16.dp))
        Button(onClick = { vm.submit(amount, key) }, enabled = !s.submitting, modifier = Modifier.fillMaxWidth()) {
            Text(if (s.submitting) "Submitting…" else "Top up")
        }
    }
}

@HiltViewModel
class TransactionsViewModel @Inject constructor(private val repo: AccountsRepository) : ViewModel() {
    data class S(val items: List<TransactionDto> = emptyList(), val loading: Boolean = true, val err: String? = null)
    private val _s = MutableStateFlow(S()); val s: StateFlow<S> = _s.asStateFlow()
    init { load() }
    fun load() = viewModelScope.launch {
        when (val r = repo.transactions()) {
            is ApiResult.Ok -> _s.value = S(items = r.value.items, loading = false)
            is ApiResult.Err -> _s.value = S(loading = false, err = r.error.userMessage())
        }
    }
}

@Composable
fun TransactionsScreen(vm: TransactionsViewModel = hiltViewModel()) {
    val s = vm.s.collectAsState().value
    when {
        s.loading -> LoadingBox()
        s.err != null -> ErrorBox(s.err, true, vm::load)
        else -> LazyColumn(Modifier.fillMaxSize().padding(16.dp)) {
            items(s.items) { t ->
                ListItem(
                    headlineContent = { Text("${t.type} ${t.amount} ${t.currency}") },
                    supportingContent = { Text(t.timestamp) },
                    trailingContent = { Text("→ ${t.balanceAfter}") },
                )
                HorizontalDivider()
            }
        }
    }
}
