package com.vulnmno.app.ui.screens.plans

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.navigation.NavHostController
import com.vulnmno.app.data.remote.AppError
import com.vulnmno.app.data.remote.dto.PlanDto
import com.vulnmno.app.data.repository.ApiResult
import com.vulnmno.app.data.repository.PlansRepository
import com.vulnmno.app.ui.navigation.Routes
import com.vulnmno.app.ui.screens.ErrorBox
import com.vulnmno.app.ui.screens.LoadingBox
import com.vulnmno.app.ui.screens.OnResume
import com.vulnmno.app.ui.screens.userMessage
import dagger.hilt.android.lifecycle.HiltViewModel
import java.util.UUID
import javax.inject.Inject
import kotlinx.coroutines.async
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

@HiltViewModel
class PlansViewModel @Inject constructor(private val repo: PlansRepository) : ViewModel() {
    data class S(val current: PlanDto? = null, val available: List<PlanDto> = emptyList(), val loading: Boolean = true, val err: String? = null)
    private val _s = MutableStateFlow(S()); val s: StateFlow<S> = _s.asStateFlow()
    fun load() = viewModelScope.launch {
        _s.update { it.copy(loading = true, err = null) }
        val c = async { repo.current() }; val a = async { repo.available() }
        _s.value = S(
            current = (c.await() as? ApiResult.Ok)?.value,
            available = (a.await() as? ApiResult.Ok)?.value?.items ?: emptyList(),
            loading = false,
        )
    }
}

@Composable
fun PlansScreen(nav: NavHostController, vm: PlansViewModel = hiltViewModel()) {
    OnResume { vm.load() }   // refetch every time this destination becomes RESUMED
    val s = vm.s.collectAsState().value
    if (s.loading) LoadingBox()
    else LazyColumn(Modifier.fillMaxSize().padding(16.dp)) {
        item {
            Text("Current plan", style = MaterialTheme.typography.titleMedium)
            s.current?.let {
                ElevatedCard(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                    Column(Modifier.padding(16.dp)) {
                        Text(it.name, style = MaterialTheme.typography.titleMedium)
                        Text("${it.monthlyPrice} ${it.currency} / month")
                        Text("Data: ${if (it.dataLimit < 0) "Unlimited" else "${it.dataLimit} MB"}")
                    }
                }
            }
            Spacer(Modifier.height(16.dp))
            Text("Available plans", style = MaterialTheme.typography.titleMedium)
        }
        items(s.available) { p ->
            ElevatedCard(
                onClick = { nav.navigate(Routes.planChange(p.planId)) },
                modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
            ) {
                Column(Modifier.padding(16.dp)) {
                    Text(p.name, style = MaterialTheme.typography.titleSmall)
                    Text("${p.monthlyPrice} ${p.currency}")
                }
            }
        }
    }
}

@HiltViewModel
class PlanChangeViewModel @Inject constructor(private val repo: PlansRepository) : ViewModel() {
    data class S(val target: PlanDto? = null, val mode: String = "immediate", val submitting: Boolean = false, val ineligible: String? = null, val error: String? = null, val done: Boolean = false)
    private val _s = MutableStateFlow(S()); val s: StateFlow<S> = _s.asStateFlow()
    fun load(planId: String) = viewModelScope.launch {
        val a = repo.available()
        if (a is ApiResult.Ok) {
            val target = a.value.items.firstOrNull { it.planId == planId }
            _s.update { it.copy(target = target, error = if (target == null) "Plan not found" else null) }
        }
    }
    fun setMode(m: String) = _s.update { it.copy(mode = m) }
    fun submit(key: String) = viewModelScope.launch {
        val target = _s.value.target ?: return@launch
        _s.update { it.copy(submitting = true, error = null, ineligible = null) }
        when (val r = repo.change(key, target.planId, _s.value.mode)) {
            is ApiResult.Ok -> _s.update { it.copy(submitting = false, done = true) }
            is ApiResult.Err -> {
                val d = r.error as? AppError.Domain
                _s.update {
                    when (d?.code) {
                        "PLAN_INELIGIBLE" -> it.copy(submitting = false, ineligible = d.rule ?: d.message)
                        else -> it.copy(submitting = false, error = r.error.userMessage())
                    }
                }
            }
        }
    }
}

@Composable
fun PlanChangeScreen(nav: NavHostController, planId: String, vm: PlanChangeViewModel = hiltViewModel()) {
    LaunchedEffect(planId) { vm.load(planId) }
    val s = vm.s.collectAsState().value
    val key = remember { UUID.randomUUID().toString() }
    LaunchedEffect(s.done) { if (s.done) nav.popBackStack() }
    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Text("Confirm plan change", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(16.dp))
        s.target?.let {
            Text(it.name, style = MaterialTheme.typography.titleMedium)
            Text("${it.monthlyPrice} ${it.currency} / month")
        }
        Spacer(Modifier.height(16.dp))
        Row {
            FilterChip(selected = s.mode == "immediate", onClick = { vm.setMode("immediate") }, label = { Text("Immediate") })
            Spacer(Modifier.width(8.dp))
            FilterChip(selected = s.mode == "scheduled", onClick = { vm.setMode("scheduled") }, label = { Text("Scheduled") })
        }
        s.ineligible?.let { Text("Not eligible: $it", color = MaterialTheme.colorScheme.error) }
        s.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        Spacer(Modifier.weight(1f))
        Button(onClick = { vm.submit(key) }, enabled = !s.submitting && s.target != null, modifier = Modifier.fillMaxWidth()) {
            Text(if (s.submitting) "Submitting…" else "Confirm")
        }
    }
}
