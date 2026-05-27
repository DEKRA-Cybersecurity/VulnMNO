package com.vulnmno.app.ui.screens.support

import android.content.Context
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.outlined.Add
import androidx.compose.material.icons.outlined.AttachFile
import androidx.compose.material.icons.outlined.Attachment
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.navigation.NavHostController
import com.vulnmno.app.data.remote.AppError
import com.vulnmno.app.data.remote.dto.TicketAttachmentDto
import com.vulnmno.app.data.remote.dto.TicketDto
import com.vulnmno.app.data.remote.dto.TicketSummaryDto
import com.vulnmno.app.data.repository.ApiResult
import com.vulnmno.app.data.repository.SupportRepository
import com.vulnmno.app.ui.navigation.Routes
import com.vulnmno.app.ui.screens.ErrorBox
import com.vulnmno.app.ui.screens.LoadingBox
import com.vulnmno.app.ui.screens.OnResume
import com.vulnmno.app.ui.screens.userMessage
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

@HiltViewModel
class SupportListViewModel @Inject constructor(private val repo: SupportRepository) : ViewModel() {
    data class S(val items: List<TicketSummaryDto> = emptyList(), val loading: Boolean = true, val err: String? = null)
    private val _s = MutableStateFlow(S()); val s: StateFlow<S> = _s.asStateFlow()
    fun load() = viewModelScope.launch {
        _s.value = when (val r = repo.list()) {
            is ApiResult.Ok -> S(items = r.value.items, loading = false)
            is ApiResult.Err -> S(loading = false, err = r.error.userMessage())
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SupportTicketsScreen(nav: NavHostController, vm: SupportListViewModel = hiltViewModel()) {
    OnResume { vm.load() }    // refresh the list after returning from NewTicket/TicketDetail
    val s = vm.s.collectAsState().value
    Scaffold(
        floatingActionButton = {
            FloatingActionButton(onClick = { nav.navigate(Routes.supportNew()) }) {
                Icon(Icons.Outlined.Add, contentDescription = "New ticket")
            }
        }
    ) { pad ->
        Box(Modifier.padding(pad).fillMaxSize()) {
            when {
                s.loading -> LoadingBox()
                s.err != null -> ErrorBox(s.err, true, vm::load)
                s.items.isEmpty() -> ErrorBox("No tickets yet", false)
                else -> LazyColumn(Modifier.fillMaxSize().padding(16.dp)) {
                    items(s.items) { t ->
                        ListItem(
                            headlineContent = { Text(t.topic) },
                            supportingContent = { Text("${t.status} • ${t.createdAt}") },
                            modifier = Modifier.fillMaxWidth(),
                            trailingContent = { Text(t.ticketId, style = MaterialTheme.typography.labelSmall) },
                            tonalElevation = 0.dp,
                            colors = ListItemDefaults.colors(),
                        )
                        HorizontalDivider(Modifier.padding(horizontal = 16.dp))
                        TextButton(onClick = { nav.navigate(Routes.ticket(t.ticketId)) }, modifier = Modifier.padding(start = 8.dp)) {
                            Text("Open")
                        }
                    }
                }
            }
        }
    }
}

@HiltViewModel
class NewTicketViewModel @Inject constructor(private val repo: SupportRepository) : ViewModel() {
    data class S(val submitting: Boolean = false, val error: String? = null, val ticketId: String? = null)
    private val _s = MutableStateFlow(S()); val s: StateFlow<S> = _s.asStateFlow()
    fun submit(topic: String, description: String) = viewModelScope.launch {
        _s.value = S(submitting = true)
        _s.value = when (val r = repo.create(topic, description)) {
            is ApiResult.Ok -> S(ticketId = r.value.ticketId)
            is ApiResult.Err -> S(error = r.error.userMessage())
        }
    }
}

@OptIn(androidx.compose.foundation.layout.ExperimentalLayoutApi::class)
@Composable
fun NewTicketScreen(nav: NavHostController, topicArg: String?, vm: NewTicketViewModel = hiltViewModel()) {
    var topic by rememberSaveable { mutableStateOf(topicArg ?: "Other") }
    var desc by rememberSaveable { mutableStateOf("") }
    val s = vm.s.collectAsState().value
    LaunchedEffect(s.ticketId) { s.ticketId?.let { nav.navigate(Routes.ticket(it)) { popUpTo(Routes.supportNew) { inclusive = true } } } }
    val topics = listOf("Billing", "Plan", "Technical", "Purchase", "Other")
    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Text("New ticket", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(16.dp))
        Text("Topic")
        // FlowRow wraps chips to the next line when the screen is too narrow — five
        // FilterChips don't fit on a Pixel 6 in a single Row, which previously squeezed
        // the last chip's text to render letter-by-letter vertically.
        androidx.compose.foundation.layout.FlowRow(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            topics.forEach { t ->
                FilterChip(selected = topic == t, onClick = { topic = t }, label = { Text(t) })
            }
        }
        Spacer(Modifier.height(16.dp))
        OutlinedTextField(value = desc, onValueChange = { desc = it }, label = { Text("Description") }, modifier = Modifier.fillMaxWidth().heightIn(min = 160.dp))
        s.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        Spacer(Modifier.weight(1f))
        Button(onClick = { vm.submit(topic, desc) }, enabled = !s.submitting && desc.length >= 5, modifier = Modifier.fillMaxWidth()) {
            Text(if (s.submitting) "Creating…" else "Create ticket")
        }
    }
}

@HiltViewModel
class TicketDetailViewModel @Inject constructor(
    private val repo: SupportRepository,
    @ApplicationContext private val ctx: Context,
) : ViewModel() {
    data class S(
        val ticket: TicketDto? = null,
        val loading: Boolean = true,
        val err: String? = null,
        val sending: Boolean = false,
        val closed: Boolean = false,
        val uploading: Boolean = false,
        val flash: String? = null,
    )
    private val _s = MutableStateFlow(S()); val s: StateFlow<S> = _s.asStateFlow()
    fun consumeFlash() { _s.update { it.copy(flash = null) } }
    fun load(id: String) = viewModelScope.launch {
        _s.value = when (val r = repo.get(id)) {
            is ApiResult.Ok -> S(ticket = r.value, loading = false, closed = r.value.status == "closed")
            is ApiResult.Err -> S(loading = false, err = r.error.userMessage())
        }
    }
    fun send(id: String, body: String) = viewModelScope.launch {
        _s.update { it.copy(sending = true) }
        when (val r = repo.addMessage(id, body)) {
            is ApiResult.Ok -> load(id)
            is ApiResult.Err -> _s.update {
                val d = r.error as? AppError.Domain
                it.copy(sending = false, closed = d?.code == "TICKET_CLOSED" || it.closed, err = r.error.userMessage())
            }
        }
        _s.update { it.copy(sending = false) }
    }
    fun close(id: String) = viewModelScope.launch {
        if (repo.close(id) is ApiResult.Ok) load(id)
    }

    fun upload(id: String, uri: Uri) = viewModelScope.launch {
        _s.update { it.copy(uploading = true) }
        val cr = ctx.contentResolver
        val mime = cr.getType(uri) ?: "application/octet-stream"
        val name = queryDisplayName(uri) ?: "upload.bin"
        val bytes = try {
            cr.openInputStream(uri)?.use { it.readBytes() } ?: ByteArray(0)
        } catch (_: Throwable) { ByteArray(0) }
        if (bytes.isEmpty()) {
            _s.update { it.copy(uploading = false, err = "Could not read file") }
            return@launch
        }
        when (val r = repo.addAttachment(id, name, mime, bytes)) {
            is ApiResult.Ok -> { _s.update { it.copy(uploading = false, flash = "Attached $name") }; load(id) }
            is ApiResult.Err -> _s.update { it.copy(uploading = false, err = r.error.userMessage()) }
        }
    }

    private fun queryDisplayName(uri: Uri): String? {
        return try {
            ctx.contentResolver.query(uri, arrayOf(android.provider.OpenableColumns.DISPLAY_NAME), null, null, null)
                ?.use { c -> if (c.moveToFirst()) c.getString(0) else null }
        } catch (_: Throwable) { null }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TicketDetailScreen(nav: NavHostController, ticketId: String, vm: TicketDetailViewModel = hiltViewModel()) {
    LaunchedEffect(ticketId) { vm.load(ticketId) }
    val s = vm.s.collectAsState().value
    var reply by rememberSaveable { mutableStateOf("") }

    val picker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        if (uri != null) vm.upload(ticketId, uri)
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Ticket $ticketId") },
                navigationIcon = {
                    IconButton(onClick = {
                        if (!nav.popBackStack()) nav.navigate(Routes.support) { popUpTo(0) }
                    }) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    if (!s.closed) {
                        IconButton(
                            onClick = { picker.launch("*/*") },
                            enabled = !s.uploading,
                        ) {
                            Icon(Icons.Outlined.AttachFile, contentDescription = "Attach file")
                        }
                    }
                },
            )
        }
    ) { pad ->
        Box(Modifier.padding(pad).fillMaxSize()) {
            when {
                s.loading -> LoadingBox()
                s.err != null -> ErrorBox(s.err, true, { vm.load(ticketId) })
                s.ticket != null -> Column(Modifier.fillMaxSize().padding(16.dp)) {
                    s.flash?.let {
                        LaunchedEffect(it) { kotlinx.coroutines.delay(2_500); vm.consumeFlash() }
                        Surface(color = MaterialTheme.colorScheme.secondaryContainer, modifier = Modifier.fillMaxWidth()) {
                            Text(it, modifier = Modifier.padding(12.dp), style = MaterialTheme.typography.bodyMedium)
                        }
                        Spacer(Modifier.height(8.dp))
                    }
                    Text(s.ticket.topic, style = MaterialTheme.typography.titleLarge)
                    Text("Status: ${s.ticket.status}")
                    Spacer(Modifier.height(8.dp))
                    LazyColumn(Modifier.weight(1f)) {
                        items(s.ticket.messages) { m ->
                            Column(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                                Text("${m.author.role}: ${m.author.displayName}", style = MaterialTheme.typography.labelSmall)
                                Text(m.body)
                            }
                        }
                        if (s.ticket.attachments.isNotEmpty()) {
                            item {
                                Spacer(Modifier.height(8.dp))
                                Text("Attachments (${s.ticket.attachments.size})", style = MaterialTheme.typography.labelLarge)
                            }
                            items(s.ticket.attachments) { att -> AttachmentRow(att) }
                        }
                    }
                    if (s.uploading) {
                        LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
                    }
                    if (s.closed) {
                        Text("Ticket closed", color = MaterialTheme.colorScheme.error)
                    } else {
                        OutlinedTextField(value = reply, onValueChange = { reply = it }, label = { Text("Reply") }, modifier = Modifier.fillMaxWidth())
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { vm.send(ticketId, reply); reply = "" }, enabled = !s.sending && reply.isNotBlank(), modifier = Modifier.weight(1f)) {
                                Text("Send")
                            }
                            OutlinedButton(onClick = { vm.close(ticketId) }, modifier = Modifier.weight(1f)) { Text("Close ticket") }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun AttachmentRow(att: TicketAttachmentDto) {
    ListItem(
        leadingContent = { Icon(Icons.Outlined.Attachment, contentDescription = null) },
        headlineContent = { Text(att.filename) },
        supportingContent = { Text("${att.contentType} • ${att.sizeBytes} B") },
    )
    HorizontalDivider()
}

