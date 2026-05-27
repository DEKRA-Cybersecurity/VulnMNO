package com.vulnmno.app.ui.screens.invoices

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.navigation.NavHostController
import com.vulnmno.app.data.remote.dto.InvoiceDto
import com.vulnmno.app.data.remote.dto.InvoiceSummaryDto
import com.vulnmno.app.data.remote.dto.RefundRequestDto
import com.vulnmno.app.data.repository.AccountsRepository
import com.vulnmno.app.data.repository.ApiResult
import com.vulnmno.app.ui.navigation.Routes
import com.vulnmno.app.ui.screens.ErrorBox
import com.vulnmno.app.ui.screens.LoadingBox
import com.vulnmno.app.ui.screens.userMessage
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

@HiltViewModel
class InvoicesViewModel @Inject constructor(private val repo: AccountsRepository) : ViewModel() {
    data class S(val items: List<InvoiceSummaryDto> = emptyList(), val loading: Boolean = true, val err: String? = null)
    private val _s = MutableStateFlow(S()); val s: StateFlow<S> = _s.asStateFlow()
    init { load() }
    fun load() = viewModelScope.launch {
        _s.value = when (val r = repo.invoices()) {
            is ApiResult.Ok -> S(items = r.value.items, loading = false)
            is ApiResult.Err -> S(loading = false, err = r.error.userMessage())
        }
    }
}

@Composable
fun InvoicesScreen(nav: NavHostController, vm: InvoicesViewModel = hiltViewModel()) {
    val s = vm.s.collectAsState().value
    when {
        s.loading -> LoadingBox()
        s.err != null -> ErrorBox(s.err, true, vm::load)
        s.items.isEmpty() -> ErrorBox("No invoices yet", false)
        else -> LazyColumn(Modifier.fillMaxSize().padding(16.dp)) {
            items(s.items) { i ->
                ElevatedCard(onClick = { nav.navigate(Routes.invoice(i.invoiceId)) }, modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                    Column(Modifier.padding(16.dp)) {
                        Text("Period ${i.period}", style = MaterialTheme.typography.titleSmall)
                        Text("${i.totalAmount} ${i.currency} • ${i.status}")
                    }
                }
            }
        }
    }
}

@HiltViewModel
class InvoiceDetailViewModel @Inject constructor(
    private val repo: AccountsRepository,
    @dagger.hilt.android.qualifiers.ApplicationContext private val ctx: android.content.Context,
) : ViewModel() {
    sealed interface S { data object Loading : S; data class Loaded(val inv: InvoiceDto) : S; data class Err(val msg: String) : S }
    private val _s = MutableStateFlow<S>(S.Loading); val s: StateFlow<S> = _s.asStateFlow()

    data class DownloadState(val downloading: Boolean = false, val fileUri: android.net.Uri? = null, val error: String? = null)
    private val _dl = MutableStateFlow(DownloadState())
    val dl: StateFlow<DownloadState> = _dl.asStateFlow()
    fun consumeDownload() { _dl.value = _dl.value.copy(fileUri = null, error = null) }

    fun load(id: String) = viewModelScope.launch {
        _s.value = when (val r = repo.invoice(id)) {
            is ApiResult.Ok -> S.Loaded(r.value); is ApiResult.Err -> S.Err(r.error.userMessage())
        }
    }

    fun download(invoiceId: String) = viewModelScope.launch {
        _dl.value = DownloadState(downloading = true)
        when (val r = repo.downloadInvoice(invoiceId)) {
            is ApiResult.Ok -> {
                val file = java.io.File(ctx.cacheDir, "invoice-$invoiceId.pdf")
                file.writeBytes(r.value)
                val uri = androidx.core.content.FileProvider.getUriForFile(
                    ctx, "${ctx.packageName}.fileprovider", file,
                )
                _dl.value = DownloadState(fileUri = uri)
            }
            is ApiResult.Err -> _dl.value = DownloadState(error = r.error.userMessage())
        }
    }
}

@Composable
fun InvoiceDetailScreen(nav: NavHostController, invoiceId: String, vm: InvoiceDetailViewModel = hiltViewModel()) {
    val ctx = androidx.compose.ui.platform.LocalContext.current
    LaunchedEffect(invoiceId) { vm.load(invoiceId) }
    val dl = vm.dl.collectAsState().value
    LaunchedEffect(dl.fileUri) {
        val uri = dl.fileUri ?: return@LaunchedEffect
        val intent = android.content.Intent(android.content.Intent.ACTION_VIEW).apply {
            setDataAndType(uri, "application/pdf")
            addFlags(android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION)
            addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        try {
            ctx.startActivity(intent)
        } catch (e: android.content.ActivityNotFoundException) {
            // No PDF viewer installed — surface a hint via state.
        }
        vm.consumeDownload()
    }
    when (val s = vm.s.collectAsState().value) {
        InvoiceDetailViewModel.S.Loading -> LoadingBox()
        is InvoiceDetailViewModel.S.Err -> ErrorBox(s.msg)
        is InvoiceDetailViewModel.S.Loaded -> Column(Modifier.fillMaxSize().padding(16.dp)) {
            Text("Invoice ${s.inv.invoiceId}", style = MaterialTheme.typography.titleLarge)
            Text("Period ${s.inv.period}")
            Text("Total: ${s.inv.totalAmount} ${s.inv.currency} • ${s.inv.status}")
            Spacer(Modifier.height(16.dp))
            Text("Line items", style = MaterialTheme.typography.titleMedium)
            s.inv.lineItems.forEach { li ->
                Row(Modifier.fillMaxWidth().padding(vertical = 4.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(li.description); Text("${li.amount} ${li.currency}")
                }
            }
            dl.error?.let { Spacer(Modifier.height(8.dp)); Text(it, color = MaterialTheme.colorScheme.error) }
            Spacer(Modifier.weight(1f))
            Button(
                onClick = { vm.download(s.inv.invoiceId) },
                enabled = !dl.downloading,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(if (dl.downloading) "Downloading…" else "Download PDF")
            }
            Spacer(Modifier.height(8.dp))
            OutlinedButton(onClick = { nav.navigate(Routes.refund("invoice", s.inv.invoiceId)) }, modifier = Modifier.fillMaxWidth()) {
                Text("Request refund")
            }
        }
    }
}

@HiltViewModel
class RefundViewModel @Inject constructor(private val repo: AccountsRepository) : ViewModel() {
    data class S(val submitting: Boolean = false, val error: String? = null, val ticketId: String? = null)
    private val _s = MutableStateFlow(S()); val s: StateFlow<S> = _s.asStateFlow()
    fun submit(targetType: String, targetId: String, reason: String) = viewModelScope.launch {
        _s.value = S(submitting = true)
        _s.value = when (val r = repo.requestRefund(RefundRequestDto(targetType, targetId, reason))) {
            is ApiResult.Ok -> S(ticketId = r.value.ticketId)
            is ApiResult.Err -> S(error = r.error.userMessage())
        }
    }
}

@Composable
fun RefundRequestScreen(nav: NavHostController, targetType: String, targetId: String, vm: RefundViewModel = hiltViewModel()) {
    var reason by rememberSaveable { mutableStateOf("") }
    val s = vm.s.collectAsState().value
    LaunchedEffect(s.ticketId) { s.ticketId?.let { nav.navigate(Routes.ticket(it)) { popUpTo(Routes.refund) { inclusive = true } } } }
    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Text("Request refund", style = MaterialTheme.typography.titleLarge)
        Text("Target: $targetType $targetId")
        Spacer(Modifier.height(16.dp))
        OutlinedTextField(value = reason, onValueChange = { reason = it }, label = { Text("Reason") }, modifier = Modifier.fillMaxWidth().heightIn(min = 120.dp))
        s.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        Spacer(Modifier.weight(1f))
        Button(onClick = { vm.submit(targetType, targetId, reason) }, enabled = !s.submitting && reason.length >= 5, modifier = Modifier.fillMaxWidth()) {
            Text(if (s.submitting) "Submitting…" else "Submit")
        }
    }
}
