from __future__ import annotations

from threading import Event, Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from lib.cluster.hosts_blocker import HostsBlocker, HostsBlockerError
from lib.cluster.ping_benchmark import PingBenchmarkResult, run_ping_benchmark
from lib.dataclasses.configs.main_config import ClusterEntry
from ui.cluster_widgets import ClusterSelectButton
from ui.widgets import DvpActionButton, SettingsOptionButton, reset_progress_bar, sync_progress_bar
from utils.admin import is_elevated

_REGIONS = ("ru", "eu", "asia", "na")
_PING_COUNT = 100


class ClusterScreen(MDScreen):
    name = "cluster"

    def __init__(self, **kwargs):
        self._region = "ru"
        self._selected: set[str] = set()
        self._blocked: set[str] = set()
        self._ping_busy = False
        self._ping_cancel = Event()
        self._ping_thread: Thread | None = None
        self._ping_batch_total = 0
        super().__init__(**kwargs)

    def on_enter(self, *_args):
        self._blocked = HostsBlocker().read_blocked()
        self.refresh_locale()
        self._sync_region_buttons()
        self._rebuild_cluster_list()
        self._sync_admin_state()
        Clock.schedule_once(lambda _dt: self._resync_buttons(), 0.05)
        Clock.schedule_once(lambda _dt: self._refresh_scroll_layout(), 0)

    def _refresh_scroll_layout(self):
        content = self.ids.get("cluster_content")
        if content is not None:
            content.height = content.minimum_height

    def refresh_locale(self):
        loc = self._locale()
        ids = self.ids

        ids.screen_title.text = loc.title
        ids.screen_hint.text = loc.description
        ids.section_regions.text = loc.sections.regions
        ids.section_clusters.text = loc.sections.clusters
        ids.section_ping.text = loc.sections.ping
        ids.section_stats.text = loc.sections.stats
        ids.section_summary.text = loc.sections.summary

        ids.btn_block.action_label = loc.actions.block
        ids.btn_unblock.action_label = loc.actions.unblock
        ids.btn_unblock_all.action_label = loc.actions.unblock_all
        ids.btn_ping.action_label = loc.actions.ping
        ids.btn_stop_ping.action_label = loc.actions.stop_ping

        ids.admin_hint.text = loc.status.admin_required if not is_elevated() else ""
        self._sync_region_buttons()
        self._rebuild_cluster_list()
        self._sync_stats_labels(None)
        self._sync_ping_summary([])
        self._sync_ping_status(None)
        self._set_ping_progress_visible(False)
        self._refresh_scroll_layout()

    def select_region(self, region: str):
        if region not in _REGIONS or self._ping_busy:
            return
        self._region = region
        self._selected.clear()
        self._sync_region_buttons()
        self._rebuild_cluster_list()

    def toggle_cluster(self, key: str):
        if self._ping_busy:
            return
        if key in self._selected:
            self._selected.discard(key)
        else:
            self._selected.add(key)
        self._sync_cluster_buttons()

    def block_selected(self):
        if self._ping_busy or not is_elevated():
            self._set_status(self._locale().status.admin_required)
            return
        hostnames = self._selected_hostnames()
        if not hostnames:
            self._set_status(self._locale().status.no_selection)
            return
        try:
            HostsBlocker().block(hostnames)
            self._blocked = HostsBlocker().read_blocked()
            self._rebuild_cluster_list()
            self._set_status(self._locale().status.blocked.format(count=len(hostnames)))
        except HostsBlockerError:
            self._set_status(self._locale().status.block_failed)

    def unblock_selected(self):
        if self._ping_busy or not is_elevated():
            self._set_status(self._locale().status.admin_required)
            return
        hostnames = self._selected_hostnames()
        if not hostnames:
            self._set_status(self._locale().status.no_selection)
            return
        try:
            HostsBlocker().unblock(hostnames)
            self._blocked = HostsBlocker().read_blocked()
            self._rebuild_cluster_list()
            self._set_status(self._locale().status.unblocked.format(count=len(hostnames)))
        except HostsBlockerError:
            self._set_status(self._locale().status.unblock_failed)

    def unblock_all(self):
        if self._ping_busy or not is_elevated():
            self._set_status(self._locale().status.admin_required)
            return
        try:
            HostsBlocker().unblock_all()
            self._blocked = set()
            self._rebuild_cluster_list()
            self._set_status(self._locale().status.unblocked_all)
        except HostsBlockerError:
            self._set_status(self._locale().status.unblock_failed)

    def start_ping_test(self):
        if self._ping_busy:
            return
        hosts = self._selected_hosts_ordered()
        if not hosts:
            self._set_status(self._locale().status.no_selection)
            return

        self._ping_busy = True
        self._ping_cancel.clear()
        self._ping_batch_total = len(hosts)
        self._sync_admin_state()
        self._sync_ping_summary([])
        self._sync_stats_labels(None)
        self._set_ping_progress_visible(True)
        self._reset_ping_progress()

        blocked_hosts = set(self._blocked)

        def worker(target_hosts: list[str], blocked: set[str]):
            results: list[PingBenchmarkResult] = []
            total_clusters = len(target_hosts)

            for cluster_index, hostname in enumerate(target_hosts, start=1):
                if self._ping_cancel.is_set():
                    break

                Clock.schedule_once(
                    lambda _dt, h=hostname, i=cluster_index, t=total_clusters: self._on_ping_cluster_started(
                        h, i, t
                    ),
                    0,
                )

                is_blocked = hostname.lower() in blocked
                result = run_ping_benchmark(
                    hostname,
                    count=_PING_COUNT,
                    blocked=is_blocked,
                    on_progress=lambda current, total, latency, i=cluster_index, t=total_clusters, h=hostname: Clock.schedule_once(
                        lambda _dt, c=current, ptotal=total, lat=latency, ci=i, ct=t, host=h: self._on_ping_progress(
                            c, ptotal, lat, host=host, cluster=ci, clusters_total=ct
                        ),
                        0,
                    ),
                    cancel_event=self._ping_cancel,
                )
                results.append(result)
                Clock.schedule_once(
                    lambda _dt, r=result, batch=results: self._on_ping_cluster_finished(r, batch),
                    0,
                )

            Clock.schedule_once(
                lambda _dt, batch=results, total=total_clusters: self._on_ping_batch_finished(
                    batch, total
                ),
                0,
            )

        self._ping_thread = Thread(
            target=worker,
            args=(hosts, blocked_hosts),
            daemon=True,
            name="cluster_ping_benchmark",
        )
        self._ping_thread.start()

    def stop_ping_test(self):
        if not self._ping_busy:
            return
        self._ping_cancel.set()
        self._set_status(self._locale().status.ping_stopping)

    def _on_ping_cluster_started(self, host: str, cluster: int, clusters_total: int):
        self._reset_ping_progress()
        self._sync_ping_status(
            "batch_running",
            host=host,
            cluster=cluster,
            clusters_total=clusters_total,
        )

    def _on_ping_progress(
        self,
        current: int,
        total: int,
        latency: float | None,
        *,
        host: str,
        cluster: int,
        clusters_total: int,
    ):
        self._sync_ping_status(
            "batch_progress",
            current=current,
            total=total,
            host=host,
            cluster=cluster,
            clusters_total=clusters_total,
        )
        self._apply_ping_progress(current, total, host)

    def _on_ping_cluster_finished(self, result: PingBenchmarkResult, results: list[PingBenchmarkResult]):
        self._sync_stats_labels(result)
        self._sync_ping_summary(results)

    def _on_ping_batch_finished(self, results: list[PingBenchmarkResult], clusters_total: int):
        self._ping_busy = False
        self._ping_thread = None
        self._sync_admin_state()
        loc = self._locale()
        cancelled = self._ping_cancel.is_set() and len(results) < clusters_total

        if cancelled:
            self._sync_ping_status("batch_stopped", done=len(results), total=clusters_total)
            self._set_status(loc.status.ping_batch_stopped.format(done=len(results), total=clusters_total))
        elif len(results) == 1:
            self._sync_ping_status("done", host=results[0].host)
            self._set_status(loc.status.ping_done.format(host=results[0].host))
        else:
            self._sync_ping_status("batch_done", count=len(results))
            self._set_status(loc.status.ping_batch_done.format(count=len(results)))

        if results:
            self._sync_stats_labels(results[-1])
            self._sync_ping_summary(results)
        self._set_ping_progress_visible(False)
        self._refresh_scroll_layout()

    def _selected_hostnames(self) -> set[str]:
        return set(self._selected_hosts_ordered())

    def _selected_hosts_ordered(self) -> list[str]:
        hostnames: list[str] = []
        for entry in self._clusters_for_region(self._region):
            key = self._cluster_key(self._region, entry)
            if key in self._selected:
                hostnames.append(entry.name.lower())
        return hostnames

    def _entry_for_key(self, key: str) -> ClusterEntry | None:
        region, _, cluster_id = key.partition(":")
        try:
            numeric_id = int(cluster_id)
        except ValueError:
            return None
        for entry in self._clusters_for_region(region):
            if entry.id == numeric_id:
                return entry
        return None

    def _clusters_for_region(self, region: str) -> list[ClusterEntry]:
        app = MDApp.get_running_app()
        if not app:
            return []
        clusters = app.config.clusters
        return list(getattr(clusters, region, []))

    def _cluster_key(self, region: str, entry: ClusterEntry) -> str:
        return f"{region}:{entry.id}"

    def _rebuild_cluster_list(self):
        container = self.ids.cluster_list
        if not container:
            return

        container.clear_widgets()
        loc = self._locale()
        for entry in self._clusters_for_region(self._region):
            key = self._cluster_key(self._region, entry)
            blocked = entry.name.lower() in self._blocked
            suffix = loc.labels.blocked_suffix if blocked else ""
            label = loc.labels.cluster_row.format(id=entry.id, name=entry.name, suffix=suffix)

            row = ClusterSelectButton(
                option_value=key,
                option_label=label,
                active=key in self._selected,
            )
            row.bind(on_release=lambda _btn, k=key: self.toggle_cluster(k))
            container.add_widget(row)

        Clock.schedule_once(lambda _dt: self._sync_cluster_buttons(), 0)
        self._refresh_scroll_layout()

    def _sync_region_buttons(self):
        loc = self._locale()
        labels = {
            "ru": loc.regions.ru,
            "eu": loc.regions.eu,
            "asia": loc.regions.asia,
            "na": loc.regions.na,
        }
        for widget in self.ids.region_row.children:
            if not isinstance(widget, SettingsOptionButton):
                continue
            widget.option_label = labels.get(widget.option_value, widget.option_value.upper())
            widget.active = widget.option_value == self._region
            widget.disabled = self._ping_busy
            widget.sync_appearance()

    def _sync_cluster_buttons(self):
        for widget in self.ids.cluster_list.children:
            if not isinstance(widget, ClusterSelectButton):
                continue
            widget.active = widget.option_value in self._selected
            widget.disabled = self._ping_busy
            widget.sync_appearance()

    def _sync_admin_state(self):
        elevated = is_elevated()
        busy = self._ping_busy
        for widget_id in ("btn_block", "btn_unblock", "btn_unblock_all"):
            btn = self.ids.get(widget_id)
            if isinstance(btn, DvpActionButton):
                btn.disabled = busy or not elevated

        for widget_id in ("btn_ping", "btn_stop_ping"):
            btn = self.ids.get(widget_id)
            if isinstance(btn, DvpActionButton):
                if widget_id == "btn_stop_ping":
                    btn.disabled = not busy
                else:
                    btn.disabled = busy

        ids = self.ids
        ids.admin_hint.text = "" if elevated else self._locale().status.admin_required

    def _reset_ping_progress(self):
        reset_progress_bar(self.ids.ping_progress_fill)

    def _apply_ping_progress(self, current: int, total: int, host: str):
        if not self._ping_busy:
            return

        loc = self._locale()
        if not loc:
            return

        sync_progress_bar(self.ids.ping_progress_fill, current, total)
        self.ids.ping_progress_label.text = loc.status.ping_progress.format(
            current=current,
            total=total,
        )

    def _set_ping_progress_visible(self, visible: bool):
        panel = self.ids.ping_progress_panel
        panel.opacity = 1 if visible else 0
        panel.disabled = not visible
        panel.height = dp(32) if visible else 0
        if visible:
            self._reset_ping_progress()
        else:
            reset_progress_bar(self.ids.ping_progress_fill)
            self.ids.ping_progress_label.text = ""
        self._refresh_scroll_layout()

    def _sync_stats_labels(self, result: PingBenchmarkResult | None):
        loc = self._locale()
        ids = self.ids
        na = loc.stats.na

        if not result:
            ids.stat_host.text = loc.stats.host.format(value=na)
            ids.stat_min.text = loc.stats.min.format(value=na)
            ids.stat_avg.text = loc.stats.avg.format(value=na)
            ids.stat_max.text = loc.stats.max.format(value=na)
            ids.stat_loss.text = loc.stats.loss.format(value=na)
            ids.stat_jitter.text = loc.stats.jitter.format(value=na)
            ids.stat_duration.text = loc.stats.duration.format(value=na)
            self._refresh_scroll_layout()
            return

        ids.stat_host.text = loc.stats.host.format(value=result.host)

        if result.status == "unavailable":
            status_value = loc.stats.status_unavailable
        elif result.status == "blocked":
            status_value = loc.stats.status_blocked
        else:
            status_value = None

        if status_value is not None:
            ids.stat_min.text = loc.stats.status.format(value=status_value)
            ids.stat_avg.text = loc.stats.avg.format(value=na)
            ids.stat_max.text = loc.stats.max.format(value=na)
            ids.stat_loss.text = loc.stats.loss.format(value=na)
            ids.stat_jitter.text = loc.stats.jitter.format(value=na)
            ids.stat_duration.text = loc.stats.duration.format(value=na)
            self._refresh_scroll_layout()
            return

        def fmt_ms(value: float | None) -> str:
            return f"{value:.1f}" if value is not None else na

        ids.stat_min.text = loc.stats.min.format(value=fmt_ms(result.min_ms))
        ids.stat_avg.text = loc.stats.avg.format(value=fmt_ms(result.avg_ms))
        ids.stat_max.text = loc.stats.max.format(value=fmt_ms(result.max_ms))
        ids.stat_loss.text = loc.stats.loss.format(value=f"{result.loss_percent:.1f}%")
        ids.stat_jitter.text = loc.stats.jitter.format(value=fmt_ms(result.jitter_ms))
        ids.stat_duration.text = loc.stats.duration.format(value=f"{result.duration_sec:.1f}s")
        self._refresh_scroll_layout()

    def _sync_ping_summary(self, results: list[PingBenchmarkResult]):
        loc = self._locale()
        label = self.ids.ping_summary
        if not results:
            label.text = ""
            self._refresh_scroll_layout()
            return

        lines = []
        na = loc.stats.na
        for result in results:
            if result.status == "unavailable":
                lines.append(loc.status.ping_summary_unavailable.format(host=result.host))
                continue
            if result.status == "blocked":
                lines.append(loc.status.ping_summary_blocked.format(host=result.host))
                continue

            min_ms = f"{result.min_ms:.1f}" if result.min_ms is not None else na
            avg_ms = f"{result.avg_ms:.1f}" if result.avg_ms is not None else na
            max_ms = f"{result.max_ms:.1f}" if result.max_ms is not None else na
            loss = f"{result.loss_percent:.1f}%"
            lines.append(
                loc.status.ping_summary_line.format(
                    host=result.host,
                    min=min_ms,
                    avg=avg_ms,
                    max=max_ms,
                    loss=loss,
                )
            )
        label.text = "\n".join(lines)
        if label.width > 0:
            label.text_size = (label.width, None)
            label.texture_update()
        self._refresh_scroll_layout()

    def _sync_ping_status(self, state: str | None, **kwargs):
        loc = self._locale()
        label = self.ids.ping_status
        if state is None:
            label.text = loc.status.ping_idle
        elif state == "running":
            label.text = loc.status.ping_running.format(host=kwargs.get("host", ""))
        elif state == "progress":
            label.text = loc.status.ping_progress.format(
                current=kwargs.get("current", 0),
                total=kwargs.get("total", _PING_COUNT),
            )
        elif state == "batch_running":
            label.text = loc.status.ping_batch_running.format(
                host=kwargs.get("host", ""),
                cluster=kwargs.get("cluster", 1),
                clusters_total=kwargs.get("clusters_total", 1),
            )
        elif state == "batch_progress":
            label.text = loc.status.ping_batch_progress.format(
                host=kwargs.get("host", ""),
                cluster=kwargs.get("cluster", 1),
                clusters_total=kwargs.get("clusters_total", 1),
                current=kwargs.get("current", 0),
                total=kwargs.get("total", _PING_COUNT),
            )
        elif state == "done":
            label.text = loc.status.ping_done.format(host=kwargs.get("host", ""))
        elif state == "batch_done":
            label.text = loc.status.ping_batch_done.format(count=kwargs.get("count", 0))
        elif state == "batch_stopped":
            label.text = loc.status.ping_batch_stopped.format(
                done=kwargs.get("done", 0),
                total=kwargs.get("total", 0),
            )
        elif state == "stopped":
            label.text = loc.status.ping_stopped

    def _set_status(self, text: str):
        self.ids.status_label.text = text

    def _resync_buttons(self):
        self._sync_region_buttons()
        self._sync_cluster_buttons()
        self._sync_admin_state()
        for widget in self.walk():
            if isinstance(widget, (DvpActionButton, SettingsOptionButton, ClusterSelectButton)):
                widget.sync_appearance()

    def _locale(self):
        app = MDApp.get_running_app()
        code = app.config.app_global.language if app else "ru"
        if app and code not in app.locales.data:
            code = "ru"
        return app.locales.data[code].main.cluster if app else None
