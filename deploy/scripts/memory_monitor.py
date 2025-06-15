#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
進階記憶體監控工具
為 Render 部署環境提供即時記憶體監控和管理
"""

import os
import sys
import time
import json
import gc
import threading
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# 調整路徑以支援從 deploy/scripts/ 目錄執行
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

@dataclass
class MemorySnapshot:
    """記憶體快照資料結構"""
    timestamp: str
    rss_mb: float
    vms_mb: float
    percent: float
    available_mb: float
    swap_mb: float
    cpu_percent: float

class MemoryMonitor:
    """進階記憶體監控器"""
    
    def __init__(self, 
                 warning_threshold: float = 85.0,  # 警告閾值 (%)
                 critical_threshold: float = 95.0,  # 危險閾值 (%)
                 cleanup_threshold: float = 90.0,   # 清理閾值 (%)
                 monitor_interval: int = 30,        # 監控間隔 (秒)
                 max_snapshots: int = 100):         # 最大快照數量
        
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.cleanup_threshold = cleanup_threshold
        self.monitor_interval = monitor_interval
        self.max_snapshots = max_snapshots
        
        self.snapshots: List[MemorySnapshot] = []
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # 設定日誌
        self.logger = self._setup_logger()
        
        # 統計資料
        self.alerts_count = 0
        self.cleanups_count = 0
        self.start_time = datetime.now()
    
    def _setup_logger(self) -> logging.Logger:
        """設定日誌記錄器"""
        logger = logging.getLogger('MemoryMonitor')
        logger.setLevel(logging.INFO)
        
        # 避免重複添加 handler
        if not logger.handlers:
            # 控制台輸出
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # 格式化
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # 檔案輸出 (如果可能)
            try:
                file_handler = logging.FileHandler('memory_monitor.log')
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except:
                pass  # 在 Render 環境中可能無法寫入檔案
        
        return logger
    
    def get_current_memory(self) -> MemorySnapshot:
        """取得當前記憶體狀況"""
        try:
            # 系統記憶體
            memory = psutil.virtual_memory()
            
            # 當前程序記憶體
            process = psutil.Process()
            process_memory = process.memory_info()
            
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 交换記憶體
            swap = psutil.swap_memory()
            
            snapshot = MemorySnapshot(
                timestamp=datetime.now().isoformat(),
                rss_mb=process_memory.rss / (1024 * 1024),
                vms_mb=process_memory.vms / (1024 * 1024),
                percent=memory.percent,
                available_mb=memory.available / (1024 * 1024),
                swap_mb=swap.used / (1024 * 1024),
                cpu_percent=cpu_percent
            )
            
            return snapshot
            
        except Exception as e:
            self.logger.error(f"取得記憶體資訊失敗: {e}")
            raise
    
    def add_snapshot(self, snapshot: MemorySnapshot):
        """添加記憶體快照"""
        self.snapshots.append(snapshot)
        
        # 限制快照數量
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots.pop(0)
        
        # 檢查警告條件
        self._check_thresholds(snapshot)
    
    def _check_thresholds(self, snapshot: MemorySnapshot):
        """檢查記憶體閾值並執行相應動作"""
        memory_percent = snapshot.percent
        
        # 危險級別 - 立即清理
        if memory_percent >= self.critical_threshold:
            self.logger.critical(f"🚨 記憶體使用危險! {memory_percent:.1f}% (RSS: {snapshot.rss_mb:.1f}MB)")
            self.force_cleanup()
            self.alerts_count += 1
        
        # 需要清理
        elif memory_percent >= self.cleanup_threshold:
            self.logger.warning(f"⚠️ 記憶體使用過高，執行清理: {memory_percent:.1f}% (RSS: {snapshot.rss_mb:.1f}MB)")
            self.cleanup_memory()
            self.alerts_count += 1
        
        # 警告級別
        elif memory_percent >= self.warning_threshold:
            self.logger.warning(f"⚠️ 記憶體使用警告: {memory_percent:.1f}% (RSS: {snapshot.rss_mb:.1f}MB)")
            self.alerts_count += 1
        
        # 正常狀況 (可選的資訊輸出)
        else:
            self.logger.debug(f"✅ 記憶體使用正常: {memory_percent:.1f}% (RSS: {snapshot.rss_mb:.1f}MB)")
    
    def cleanup_memory(self):
        """執行記憶體清理"""
        try:
            self.logger.info("🧹 開始記憶體清理...")
            
            # 執行垃圾收集
            collected = gc.collect()
            
            # 清理快照歷史 (保留最近50個)
            if len(self.snapshots) > 50:
                self.snapshots = self.snapshots[-50:]
            
            self.logger.info(f"✅ 記憶體清理完成，回收 {collected} 個物件")
            self.cleanups_count += 1
            
        except Exception as e:
            self.logger.error(f"記憶體清理失敗: {e}")
    
    def force_cleanup(self):
        """強制記憶體清理 (危險情況下使用)"""
        try:
            self.logger.info("🚨 執行強制記憶體清理...")
            
            # 多次垃圾收集
            total_collected = 0
            for _ in range(3):
                collected = gc.collect()
                total_collected += collected
                time.sleep(0.1)
            
            # 大幅縮減快照歷史
            self.snapshots = self.snapshots[-20:]
            
            # 嘗試清理可能的大型快取
            try:
                # 如果有全域快取變數，在這裡清理
                if 'vector_store' in globals():
                    globals()['vector_store'].clear_cache()
                if 'embedder' in globals():
                    globals()['embedder'].clear_cache()
            except:
                pass
            
            self.logger.info(f"✅ 強制清理完成，回收 {total_collected} 個物件")
            
        except Exception as e:
            self.logger.error(f"強制記憶體清理失敗: {e}")
    
    def start_monitoring(self):
        """開始背景監控"""
        if self.is_monitoring:
            self.logger.warning("監控已經在執行中")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info(f"🔍 開始記憶體監控 (間隔: {self.monitor_interval}秒)")
    
    def stop_monitoring(self):
        """停止背景監控"""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        self.logger.info("⏹️ 記憶體監控已停止")
    
    def _monitor_loop(self):
        """監控循環"""
        while self.is_monitoring:
            try:
                snapshot = self.get_current_memory()
                self.add_snapshot(snapshot)
                time.sleep(self.monitor_interval)
            except Exception as e:
                self.logger.error(f"監控循環錯誤: {e}")
                time.sleep(self.monitor_interval)
    
    def get_statistics(self) -> Dict[str, Any]:
        """取得監控統計資料"""
        if not self.snapshots:
            return {"error": "沒有監控資料"}
        
        # 計算統計值
        memory_values = [s.percent for s in self.snapshots]
        rss_values = [s.rss_mb for s in self.snapshots]
        
        current_snapshot = self.snapshots[-1]
        uptime = datetime.now() - self.start_time
        
        stats = {
            "current": {
                "memory_percent": current_snapshot.percent,
                "rss_mb": current_snapshot.rss_mb,
                "vms_mb": current_snapshot.vms_mb,
                "available_mb": current_snapshot.available_mb,
                "cpu_percent": current_snapshot.cpu_percent
            },
            "statistics": {
                "avg_memory_percent": sum(memory_values) / len(memory_values),
                "max_memory_percent": max(memory_values),
                "min_memory_percent": min(memory_values),
                "avg_rss_mb": sum(rss_values) / len(rss_values),
                "max_rss_mb": max(rss_values),
                "min_rss_mb": min(rss_values)
            },
            "monitoring": {
                "uptime_seconds": uptime.total_seconds(),
                "snapshots_count": len(self.snapshots),
                "alerts_count": self.alerts_count,
                "cleanups_count": self.cleanups_count,
                "is_monitoring": self.is_monitoring
            },
            "thresholds": {
                "warning": self.warning_threshold,
                "cleanup": self.cleanup_threshold,
                "critical": self.critical_threshold
            }
        }
        
        return stats
    
    def export_data(self, filepath: str = None) -> str:
        """匯出監控資料"""
        try:
            data = {
                "export_time": datetime.now().isoformat(),
                "statistics": self.get_statistics(),
                "snapshots": [asdict(s) for s in self.snapshots]
            }
            
            json_data = json.dumps(data, indent=2, ensure_ascii=False)
            
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(json_data)
                self.logger.info(f"📊 監控資料已匯出至: {filepath}")
            
            return json_data
            
        except Exception as e:
            self.logger.error(f"匯出資料失敗: {e}")
            return "{\"error\": \"匯出失敗\"}"
    
    def print_status(self):
        """列印當前狀態"""
        try:
            current = self.get_current_memory()
            stats = self.get_statistics()
            
            print("\n" + "="*60)
            print("📊 記憶體監控狀態")
            print("="*60)
            
            print(f"🕐 當前時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⚡ 系統記憶體: {current.percent:.1f}% ({current.available_mb:.1f}MB 可用)")
            print(f"🔧 程序記憶體: RSS {current.rss_mb:.1f}MB, VMS {current.vms_mb:.1f}MB")
            print(f"💾 交換記憶體: {current.swap_mb:.1f}MB")
            print(f"💻 CPU 使用率: {current.cpu_percent:.1f}%")
            
            if 'monitoring' in stats:
                monitoring = stats['monitoring']
                print(f"\n📈 監控統計:")
                print(f"  運行時間: {monitoring['uptime_seconds']:.0f}秒")
                print(f"  快照數量: {monitoring['snapshots_count']}")
                print(f"  警告次數: {monitoring['alerts_count']}")
                print(f"  清理次數: {monitoring['cleanups_count']}")
                print(f"  監控狀態: {'🟢 運行中' if monitoring['is_monitoring'] else '🔴 已停止'}")
            
            print(f"\n⚠️ 閾值設定:")
            print(f"  警告: {self.warning_threshold}%")
            print(f"  清理: {self.cleanup_threshold}%")
            print(f"  危險: {self.critical_threshold}%")
            
        except Exception as e:
            print(f"❌ 狀態顯示失敗: {e}")

# 全域監控器實例
_global_monitor: Optional[MemoryMonitor] = None

def get_monitor() -> MemoryMonitor:
    """取得全域監控器實例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = MemoryMonitor()
    return _global_monitor

def start_monitoring():
    """啟動監控"""
    monitor = get_monitor()
    monitor.start_monitoring()

def stop_monitoring():
    """停止監控"""
    monitor = get_monitor()
    monitor.stop_monitoring()

def get_memory_stats() -> Dict[str, Any]:
    """取得記憶體統計"""
    monitor = get_monitor()
    return monitor.get_statistics()

def cleanup_memory():
    """執行記憶體清理"""
    monitor = get_monitor()
    monitor.cleanup_memory()

def main():
    """主函數 - 命令列工具"""
    import argparse
    
    parser = argparse.ArgumentParser(description='記憶體監控工具')
    parser.add_argument('--start', action='store_true', help='開始監控')
    parser.add_argument('--status', action='store_true', help='顯示狀態')
    parser.add_argument('--cleanup', action='store_true', help='執行清理')
    parser.add_argument('--export', type=str, help='匯出資料到檔案')
    parser.add_argument('--interval', type=int, default=30, help='監控間隔(秒)')
    parser.add_argument('--warning', type=float, default=85.0, help='警告閾值(%)')
    parser.add_argument('--critical', type=float, default=95.0, help='危險閾值(%)')
    
    args = parser.parse_args()
    
    # 建立監控器
    monitor = MemoryMonitor(
        warning_threshold=args.warning,
        critical_threshold=args.critical,
        monitor_interval=args.interval
    )
    
    try:
        if args.start:
            print("🚀 啟動記憶體監控...")
            monitor.start_monitoring()
            
            # 持續運行直到中斷
            try:
                while True:
                    time.sleep(60)  # 每分鐘顯示一次狀態
                    monitor.print_status()
            except KeyboardInterrupt:
                print("\n⏹️ 收到中斷信號，停止監控...")
                monitor.stop_monitoring()
        
        elif args.status:
            monitor.print_status()
        
        elif args.cleanup:
            print("🧹 執行記憶體清理...")
            monitor.cleanup_memory()
        
        elif args.export:
            print(f"📊 匯出監控資料到: {args.export}")
            monitor.export_data(args.export)
        
        else:
            # 預設顯示狀態
            monitor.print_status()
    
    except Exception as e:
        print(f"❌ 執行失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 