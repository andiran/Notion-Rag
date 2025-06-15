#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render 部署前系統檢查腳本
檢查部署相容性和必要設定
"""

import os
import sys
import subprocess
import pkg_resources
from typing import Dict, List, Tuple, Any

# 調整路徑以支援從 deploy/scripts/ 目錄執行
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

class DeploymentChecker:
    """部署檢查器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.checks_passed = 0
        self.total_checks = 0
    
    def check_python_version(self) -> bool:
        """檢查 Python 版本"""
        self.total_checks += 1
        print("🔍 檢查 Python 版本...")
        
        current_version = sys.version_info
        min_version = (3, 8)
        max_version = (3, 12)
        
        if current_version >= min_version and current_version < max_version:
            print(f"✅ Python 版本: {current_version.major}.{current_version.minor}.{current_version.micro}")
            self.checks_passed += 1
            return True
        else:
            error_msg = f"❌ Python 版本不相容: {current_version.major}.{current_version.minor}.{current_version.micro}"
            error_msg += f" (支援範圍: {min_version[0]}.{min_version[1]}+ to {max_version[0]}.{max_version[1]}-)"
            self.errors.append(error_msg)
            print(error_msg)
            return False
    
    def check_required_packages(self) -> bool:
        """檢查必要套件"""
        self.total_checks += 1
        print("🔍 檢查必要套件...")
        
        required_packages = [
            'flask',
            'line-bot-sdk',
            'sentence-transformers',
            'faiss-cpu',
            'numpy',
            'requests',
            'python-dotenv',
            'torch',
            'psutil'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                pkg_resources.get_distribution(package)
                print(f"  ✅ {package}")
            except pkg_resources.DistributionNotFound:
                missing_packages.append(package)
                print(f"  ❌ {package} (未安裝)")
        
        if not missing_packages:
            print("✅ 所有必要套件已安裝")
            self.checks_passed += 1
            return True
        else:
            error_msg = f"❌ 缺少必要套件: {', '.join(missing_packages)}"
            self.errors.append(error_msg)
            print(error_msg)
            return False
    
    def check_environment_variables(self) -> bool:
        """檢查環境變數"""
        self.total_checks += 1
        print("🔍 檢查環境變數...")
        
        required_vars = [
            'NOTION_TOKEN',
            'NOTION_PAGE_ID',
            'LINE_CHANNEL_SECRET',
            'LINE_CHANNEL_ACCESS_TOKEN'
        ]
        
        optional_vars = [
            'OPENAI_API_KEY',
            'USE_OPENAI',
            'RENDER_DEPLOYMENT',
            'MEMORY_LIMIT',
            'USE_MEMORY_STORAGE'
        ]
        
        missing_required = []
        missing_optional = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_required.append(var)
                print(f"  ❌ {var} (必要)")
            else:
                print(f"  ✅ {var}")
        
        for var in optional_vars:
            if not os.getenv(var):
                missing_optional.append(var)
                print(f"  ⚠️ {var} (可選)")
            else:
                print(f"  ✅ {var}")
        
        if not missing_required:
            print("✅ 所有必要環境變數已設定")
            if missing_optional:
                warning_msg = f"⚠️ 可選環境變數未設定: {', '.join(missing_optional)}"
                self.warnings.append(warning_msg)
                print(warning_msg)
            self.checks_passed += 1
            return True
        else:
            error_msg = f"❌ 缺少必要環境變數: {', '.join(missing_required)}"
            self.errors.append(error_msg)
            print(error_msg)
            return False
    
    def check_memory_requirements(self) -> bool:
        """檢查記憶體需求"""
        self.total_checks += 1
        print("🔍 檢查記憶體需求...")
        
        try:
            import psutil
            available_memory = psutil.virtual_memory().available / (1024 * 1024)  # MB
            
            # Render 免費層限制
            render_memory_limit = 512  # MB
            recommended_minimum = 400   # MB
            
            print(f"  可用記憶體: {available_memory:.0f} MB")
            print(f"  Render 限制: {render_memory_limit} MB")
            
            if available_memory >= recommended_minimum:
                print("✅ 記憶體需求滿足")
                self.checks_passed += 1
                return True
            else:
                warning_msg = f"⚠️ 當前可用記憶體可能不足，建議至少 {recommended_minimum} MB"
                self.warnings.append(warning_msg)
                print(warning_msg)
                self.checks_passed += 1  # 這是警告，不是錯誤
                return True
                
        except ImportError:
            warning_msg = "⚠️ 無法檢查記憶體狀況 (psutil 未安裝)"
            self.warnings.append(warning_msg)
            print(warning_msg)
            self.checks_passed += 1
            return True
        except Exception as e:
            error_msg = f"❌ 記憶體檢查失敗: {e}"
            self.errors.append(error_msg)
            print(error_msg)
            return False
    
    def check_file_structure(self) -> bool:
        """檢查專案檔案結構"""
        self.total_checks += 1
        print("🔍 檢查專案檔案結構...")
        
        # 調整為從專案根目錄檢查
        project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
        
        required_files = [
            'linebot_app.py',
            'requirements.txt',
            'config/settings.py',
            'core/embedder.py',
            'core/vector_store.py',
            'services/linebot_handler.py',
            'render.yaml',
            'deploy/Dockerfile'
        ]
        
        required_dirs = [
            'config',
            'core',
            'services',
            'deploy'
        ]
        
        missing_files = []
        missing_dirs = []
        
        # 切換到專案根目錄進行檢查
        original_cwd = os.getcwd()
        os.chdir(project_root)
        
        try:
            for file_path in required_files:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
                    print(f"  ❌ {file_path}")
                else:
                    print(f"  ✅ {file_path}")
            
            for dir_path in required_dirs:
                if not os.path.isdir(dir_path):
                    missing_dirs.append(dir_path)
                    print(f"  ❌ {dir_path}/")
                else:
                    print(f"  ✅ {dir_path}/")
        finally:
            # 恢復原來的工作目錄
            os.chdir(original_cwd)
        
        if not missing_files and not missing_dirs:
            print("✅ 專案檔案結構完整")
            self.checks_passed += 1
            return True
        else:
            error_items = missing_files + [f"{d}/" for d in missing_dirs]
            error_msg = f"❌ 缺少必要檔案/目錄: {', '.join(error_items)}"
            self.errors.append(error_msg)
            print(error_msg)
            return False
    
    def check_render_specific_settings(self) -> bool:
        """檢查 Render 特定設定"""
        self.total_checks += 1
        print("🔍 檢查 Render 特定設定...")
        
        render_settings = {
            'RENDER_DEPLOYMENT': 'true',
            'USE_MEMORY_STORAGE': 'true',
            'FLASK_HOST': '0.0.0.0',
            'FLASK_PORT': '10000'
        }
        
        issues = []
        
        for key, expected_value in render_settings.items():
            actual_value = os.getenv(key)
            if actual_value != expected_value:
                issues.append(f"{key}={actual_value} (建議: {expected_value})")
                print(f"  ⚠️ {key}: {actual_value} (建議: {expected_value})")
            else:
                print(f"  ✅ {key}: {actual_value}")
        
        if not issues:
            print("✅ Render 設定最佳化")
            self.checks_passed += 1
            return True
        else:
            warning_msg = f"⚠️ Render 設定建議調整: {', '.join(issues)}"
            self.warnings.append(warning_msg)
            print(warning_msg)
            self.checks_passed += 1  # 這是建議，不是錯誤
            return True
    
    def generate_report(self) -> Dict[str, Any]:
        """生成檢查報告"""
        print("\n" + "="*60)
        print("📋 部署檢查報告")
        print("="*60)
        
        success_rate = (self.checks_passed / self.total_checks * 100) if self.total_checks > 0 else 0
        
        report = {
            'total_checks': self.total_checks,
            'checks_passed': self.checks_passed,
            'success_rate': success_rate,
            'errors': self.errors,
            'warnings': self.warnings,
            'ready_for_deployment': len(self.errors) == 0
        }
        
        print(f"總檢查項目: {self.total_checks}")
        print(f"通過項目: {self.checks_passed}")
        print(f"成功率: {success_rate:.1f}%")
        
        if self.errors:
            print(f"\n❌ 錯誤 ({len(self.errors)} 項):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️ 警告 ({len(self.warnings)} 項):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        print(f"\n🚀 部署狀態: {'✅ 準備就緒' if report['ready_for_deployment'] else '❌ 需要修正'}")
        
        return report
    
    def run_all_checks(self) -> Dict[str, Any]:
        """執行所有檢查"""
        print("🚀 開始 Render 部署前檢查...")
        print("="*60)
        
        # 執行所有檢查
        self.check_python_version()
        self.check_required_packages()
        self.check_environment_variables()
        self.check_memory_requirements()
        self.check_file_structure()
        self.check_render_specific_settings()
        
        # 生成報告
        return self.generate_report()

def main():
    """主函數"""
    checker = DeploymentChecker()
    report = checker.run_all_checks()
    
    # 根據結果返回適當的退出代碼
    if report['ready_for_deployment']:
        print("\n🎉 系統已準備好部署到 Render！")
        sys.exit(0)
    else:
        print("\n❌ 請修正錯誤後再嘗試部署。")
        sys.exit(1)

if __name__ == "__main__":
    main() 