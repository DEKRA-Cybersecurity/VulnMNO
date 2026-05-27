package com.vulnmno.app.ui.screens.usage

import android.content.Context
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.FileDownload
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.vulnmno.app.data.remote.dto.UsageRecordDto
import com.vulnmno.app.data.repository.ApiResult
import com.vulnmno.app.data.repository.UsageRepository
import com.vulnmno.app.ui.screens.ErrorBox
import com.vulnmno.app.ui.screens.LoadingBox
import com.vulnmno.app.ui.screens.userMessage
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

enum class UsageTab { Calls, Sms, Data, Roaming }

@HiltViewModel
class UsageViewModel @Inject constructor(
    private val repo: UsageRepository,
    @ApplicationContext private val ctx: Context,
) : ViewModel() {
    data class S(
        val tab: UsageTab = UsageTab.Calls,
        val items: List<UsageRecordDto> = emptyList(),
        val loading: Boolean = true,
        val err: String? = null,
    )

    data class ExportState(
        val exporting: Boolean = false,
        val fileUri: android.net.Uri? = null,
        val error: String? = null,
    )

    private val _s = MutableStateFlow(S()); val s: StateFlow<S> = _s.asStateFlow()
    private val _ex = MutableStateFlow(ExportState()); val ex: StateFlow<ExportState> = _ex.asStateFlow()

    init { load() }
    fun select(tab: UsageTab) { _s.update { it.copy(tab = tab) }; load() }
    fun consumeExport() { _ex.value = ExportState() }

    fun load() = viewModelScope.launch {
        _s.update { it.copy(loading = true, err = null) }
        val r = when (_s.value.tab) {
            UsageTab.Calls -> repo.calls()
            UsageTab.Sms -> repo.sms()
            UsageTab.Data -> repo.data()
            UsageTab.Roaming -> repo.roaming()
        }
        _s.update {
            when (r) {
                is ApiResult.Ok -> it.copy(items = r.value.items, loading = false)
                is ApiResult.Err -> it.copy(loading = false, err = r.error.userMessage())
            }
        }
    }

    fun exportCsv() = viewModelScope.launch {
        _ex.value = ExportState(exporting = true)
        when (val r = repo.export("csv")) {
            is ApiResult.Ok -> {
                val ts = System.currentTimeMillis()
                val file = java.io.File(ctx.cacheDir, "usage-$ts.csv")
                file.writeBytes(r.value)
                val uri = androidx.core.content.FileProvider.getUriForFile(
                    ctx, "${ctx.packageName}.fileprovider", file,
                )
                _ex.value = ExportState(fileUri = uri)
            }
            is ApiResult.Err -> _ex.value = ExportState(error = r.error.userMessage())
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun UsageScreen(vm: UsageViewModel = hiltViewModel()) {
    val s = vm.s.collectAsState().value
    val ex = vm.ex.collectAsState().value
    val ctx = LocalContext.current

    LaunchedEffect(ex.fileUri) {
        val uri = ex.fileUri ?: return@LaunchedEffect
        val intent = android.content.Intent(android.content.Intent.ACTION_VIEW).apply {
            setDataAndType(uri, "text/csv")
            addFlags(android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION)
            addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        try {
            ctx.startActivity(android.content.Intent.createChooser(intent, "Open usage CSV"))
        } catch (_: android.content.ActivityNotFoundException) {
            // No viewer available — file is still on disk in cacheDir.
        }
        vm.consumeExport()
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Usage") },
                actions = {
                    IconButton(onClick = vm::exportCsv, enabled = !ex.exporting) {
                        Icon(Icons.Outlined.FileDownload, contentDescription = "Export CSV")
                    }
                },
            )
        },
    ) { pad ->
        Column(Modifier.padding(pad).fillMaxSize()) {
            TabRow(selectedTabIndex = s.tab.ordinal) {
                UsageTab.values().forEach { tab ->
                    Tab(selected = s.tab == tab, onClick = { vm.select(tab) }, text = { Text(tab.name) })
                }
            }
            ex.error?.let {
                Surface(color = MaterialTheme.colorScheme.errorContainer, modifier = Modifier.fillMaxWidth()) {
                    Text(it, Modifier.padding(12.dp), style = MaterialTheme.typography.bodySmall)
                }
            }
            when {
                s.loading -> LoadingBox()
                s.err != null -> ErrorBox(s.err, true, vm::load)
                s.items.isEmpty() -> ErrorBox("No usage in this period", false)
                else -> LazyColumn(Modifier.fillMaxSize().padding(16.dp)) {
                    items(s.items) { u ->
                        ListItem(
                            headlineContent = { Text(u.destination ?: u.type) },
                            supportingContent = { Text("${u.startedAt} • ${u.cost} ${u.currency}") },
                            trailingContent = { Text(u.durationSeconds?.let { "${it}s" } ?: u.volumeMegabytes?.toPlainString()?.let { "$it MB" } ?: "") }
                        )
                        HorizontalDivider()
                    }
                }
            }
        }
    }
}
