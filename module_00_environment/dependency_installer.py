
"""
依赖安装器模块
负责自动检测和安装系统所需的依赖包
"""

import subprocess
import sys
import importlib
import os
import venv
from typing import Dict, List, Tuple, Optional
from pathlib import Path

from common.logging_system import setup_logger
from common.exceptions import QuantSystemError

logger = setup_logger("dependency_installer")

class DependencyInstaller:
    """依赖安装器类"""
    
    # 核心依赖包列表
    CORE_DEPENDENCIES = {
        "numpy": "1.24.0",
        "pandas": "2.0.0", 
        "polars": "0.19.0",
        "torch": "2.0.0",
        "pydantic": "2.4.0",
        "akshare": "1.11.0",
        "yfinance": "0.2.30",
        "TA-Lib": "0.4.28",
        "plotly": "5.17.0",
        "matplotlib": "3.7.0",
        "seaborn": "0.12.0",
        "fastapi": "0.104.0",
        "uvicorn": "0.23.0",
        "loguru": "0.7.0",
        "psutil": "5.9.0",
        "scipy": "1.10.0",
        "scikit-learn": "1.3.0",
        "duckdb": "0.8.0",
        "PyYAML": "6.0",
        "pytest": "7.4.0",
        "pytest-asyncio": "0.21.0",
    }
    
    # 可选依赖包
    OPTIONAL_DEPENDENCIES = {
        "transformers": "4.35.0",
        "requests": "2.31.0",
        "aiohttp": "3.8.0",
        "redis": "4.6.0",
        "kafka-python": "2.0.2",
        "celery": "5.3.0",
        "sqlalchemy": "2.0.0",
        "alembic": "1.12.0",
    }
    
    def __init__(self, use_uv: bool = True, venv_path: str = ".venv"):
        """初始化依赖安装器
        
        Args:
            use_uv: 是否使用uv包管理器
            venv_path: 虚拟环境路径
        """
        self.use_uv = use_uv
        self.venv_path = Path(venv_path)
        self.installed_packages: Dict[str, str] = {}
        self.failed_packages: List[str] = []
        self.python_executable = None
        self._setup_virtual_environment()
        
    def _setup_virtual_environment(self):
        """设置虚拟环境"""
        try:
            if not self.venv_path.exists():
                logger.info(f"Creating virtual environment at {self.venv_path}")
                
                # 检查uv是否可用
                uv_available = False
                try:
                    result = subprocess.run(["uv", "--version"], capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        uv_available = True
                        logger.info(f"Using uv: {result.stdout.strip()}")
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    logger.info("uv not available, using standard venv")
                
                if uv_available:
                    # 使用uv创建虚拟环境
                    cmd = ["uv", "venv", str(self.venv_path)]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                    if result.returncode == 0:
                        logger.info("Virtual environment created successfully with uv")
                    else:
                        logger.warning(f"uv failed: {result.stderr}, falling back to standard venv")
                        venv.create(self.venv_path, with_pip=True)
                        logger.info("Virtual environment created successfully with standard venv")
                else:
                    venv.create(self.venv_path, with_pip=True)
                    logger.info("Virtual environment created successfully with standard venv")
            else:
                logger.info(f"Using existing virtual environment at {self.venv_path}")
            
            # 设置Python可执行文件路径
            if os.name == 'nt':  # Windows
                self.python_executable = self.venv_path / "Scripts" / "python.exe"
            else:  # Unix/Linux/macOS
                self.python_executable = self.venv_path / "bin" / "python"
                
            if not self.python_executable.exists():
                raise FileNotFoundError(f"Python executable not found at {self.python_executable}")
                
            logger.info(f"Using Python executable: {self.python_executable}")
            
        except Exception as e:
            logger.error(f"Failed to setup virtual environment: {e}")
            raise
    
    def check_package_installed(self, package_name: str) -> Tuple[bool, Optional[str]]:
        """检查包是否已安装
        
        Args:
            package_name: 包名
            
        Returns:
            (是否已安装, 版本号)
        """
        try:
            # 使用虚拟环境中的Python检查包
            cmd = [str(self.python_executable), "-c", f"import {self._get_import_name(package_name)}; print(getattr({self._get_import_name(package_name)}, '__version__', 'unknown'))"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                version = result.stdout.strip()
                return True, version
            else:
                return False, None
                
        except Exception as e:
            logger.warning(f"Error checking package {package_name}: {e}")
            return False, None
            
    def install_package(self, package_name: str, version: Optional[str] = None) -> bool:
        """安装单个包
        
        Args:
            package_name: 包名
            version: 版本号
            
        Returns:
            是否安装成功
        """
        try:
            # 检查是否已安装
            is_installed, current_version = self.check_package_installed(package_name)
            if is_installed:
                logger.info(f"Package {package_name} already installed (version: {current_version})")
                self.installed_packages[package_name] = current_version
                return True
                
            # 构建安装命令
            if version:
                package_spec = f"{package_name}>={version}"
            else:
                package_spec = package_name
                
            # 检查uv是否可用
            use_uv = self.use_uv
            if use_uv:
                try:
                    # 尝试使用uv命令
                    uv_cmd = ["uv", "--version"]
                    subprocess.run(uv_cmd, capture_output=True, timeout=10)
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    # 如果uv命令不可用，尝试使用python -m uv
                    try:
                        uv_cmd = [str(self.python_executable), "-m", "uv", "--version"]
                        subprocess.run(uv_cmd, capture_output=True, timeout=10)
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        use_uv = False
                        logger.warning("uv not available, falling back to pip")
            
            if use_uv:
                try:
                    # 尝试直接使用uv命令
                    cmd = ["uv", "pip", "install", package_spec, "--python", str(self.python_executable)]
                except FileNotFoundError:
                    # 回退到python -m uv
                    cmd = [str(self.python_executable), "-m", "uv", "pip", "install", package_spec]
            else:
                cmd = [str(self.python_executable), "-m", "pip", "install", package_spec]
                
            logger.info(f"Installing {package_spec}...")
            
            # 执行安装
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully installed {package_spec}")
                self.installed_packages[package_name] = version or "latest"
                return True
            else:
                logger.error(f"Failed to install {package_spec}: {result.stderr}")
                self.failed_packages.append(package_name)
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout while installing {package_name}")
            self.failed_packages.append(package_name)
            return False
        except Exception as e:
            logger.error(f"Error installing {package_name}: {e}")
            self.failed_packages.append(package_name)
            return False
            
    def install_core_dependencies(self) -> bool:
        """安装核心依赖包
        
        Returns:
            是否全部安装成功
        """
        logger.info("Installing core dependencies...")
        success_count = 0
        total_count = len(self.CORE_DEPENDENCIES)
        
        for package_name, version in self.CORE_DEPENDENCIES.items():
            if self.install_package(package_name, version):
                success_count += 1
                
        success_rate = success_count / total_count
        logger.info(f"Core dependencies installation completed: {success_count}/{total_count} ({success_rate:.1%})")
        
        return success_rate >= 0.8  # 80%以上成功认为安装成功
        
    def install_optional_dependencies(self) -> bool:
        """安装可选依赖包
        
        Returns:
            是否全部安装成功
        """
        logger.info("Installing optional dependencies...")
        success_count = 0
        total_count = len(self.OPTIONAL_DEPENDENCIES)
        
        for package_name, version in self.OPTIONAL_DEPENDENCIES.items():
            if self.install_package(package_name, version):
                success_count += 1
                
        success_rate = success_count / total_count
        logger.info(f"Optional dependencies installation completed: {success_count}/{total_count} ({success_rate:.1%})")
        
        return success_rate >= 0.5  # 50%以上成功认为安装成功
        
    def install_from_requirements(self, requirements_file: str = "requirements.txt") -> bool:
        """从requirements文件安装依赖
        
        Args:
            requirements_file: requirements文件路径
            
        Returns:
            是否安装成功
        """
        requirements_path = Path(requirements_file)
        if not requirements_path.exists():
            logger.warning(f"Requirements file not found: {requirements_file}")
            return False
            
        try:
            # 检查uv是否可用
            use_uv = self.use_uv
            if use_uv:
                try:
                    # 尝试使用uv命令
                    uv_cmd = ["uv", "--version"]
                    subprocess.run(uv_cmd, capture_output=True, timeout=10)
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    # 如果uv命令不可用，尝试使用python -m uv
                    try:
                        uv_cmd = [str(self.python_executable), "-m", "uv", "--version"]
                        subprocess.run(uv_cmd, capture_output=True, timeout=10)
                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        use_uv = False
                        logger.warning("uv not available, falling back to pip")
            
            if use_uv:
                try:
                    # 尝试直接使用uv命令
                    cmd = ["uv", "pip", "install", "-r", str(requirements_path), "--python", str(self.python_executable)]
                except FileNotFoundError:
                    # 回退到python -m uv
                    cmd = [str(self.python_executable), "-m", "uv", "pip", "install", "-r", str(requirements_path)]
            else:
                cmd = [str(self.python_executable), "-m", "pip", "install", "-r", str(requirements_path)]
                
            logger.info(f"Installing from {requirements_file}...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully installed from {requirements_file}")
                return True
            else:
                logger.error(f"Failed to install from {requirements_file}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout while installing from {requirements_file}")
            return False
        except Exception as e:
            logger.error(f"Error installing from {requirements_file}: {e}")
            return False
            
    def upgrade_package(self, package_name: str) -> bool:
        """升级包到最新版本
        
        Args:
            package_name: 包名
            
        Returns:
            是否升级成功
        """
        try:
            if self.use_uv:
                try:
                    # 尝试直接使用uv命令
                    cmd = ["uv", "pip", "install", "--upgrade", package_name, "--python", str(self.python_executable)]
                except FileNotFoundError:
                    # 回退到python -m uv
                    cmd = [str(self.python_executable), "-m", "uv", "pip", "install", "--upgrade", package_name]
            else:
                cmd = [str(self.python_executable), "-m", "pip", "install", "--upgrade", package_name]
                
            logger.info(f"Upgrading {package_name}...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully upgraded {package_name}")
                return True
            else:
                logger.error(f"Failed to upgrade {package_name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error upgrading {package_name}: {e}")
            return False
            
    def get_installation_report(self) -> Dict[str, any]:
        """获取安装报告
        
        Returns:
            安装报告字典
        """
        return {
            "installed_packages": self.installed_packages,
            "failed_packages": self.failed_packages,
            "total_installed": len(self.installed_packages),
            "total_failed": len(self.failed_packages),
            "success_rate": len(self.installed_packages) / (len(self.installed_packages) + len(self.failed_packages)) if (len(self.installed_packages) + len(self.failed_packages)) > 0 else 0.0
        }
        
    def _get_import_name(self, package_name: str) -> str:
        """获取包的导入名称
        
        Args:
            package_name: 包名
            
        Returns:
            导入名称
        """
        # 包名映射
        name_mapping = {
            "TA-Lib": "talib",
            "PyYAML": "yaml",
            "scikit-learn": "sklearn",
        }
        
        return name_mapping.get(package_name, package_name)

# 模块级别函数
def auto_install_dependencies(use_uv: bool = True, install_optional: bool = False, venv_path: str = ".venv") -> bool:
    """自动安装依赖的便捷函数
    
    Args:
        use_uv: 是否使用uv包管理器
        install_optional: 是否安装可选依赖
        venv_path: 虚拟环境路径
        
    Returns:
        是否安装成功
    """
    installer = DependencyInstaller(use_uv=use_uv, venv_path=venv_path)
    
    # 首先尝试从requirements文件安装
    if installer.install_from_requirements():
        logger.info("Dependencies installed from requirements.txt")
        return True
    
    # 如果requirements文件安装失败，则逐个安装核心依赖
    core_success = installer.install_core_dependencies()
    
    if install_optional:
        optional_success = installer.install_optional_dependencies()
        return core_success and optional_success
    
    return core_success

def check_and_install_missing_dependencies(venv_path: str = ".venv") -> bool:
    """检查并安装缺失的依赖
    
    Args:
        venv_path: 虚拟环境路径
        
    Returns:
        是否所有依赖都已安装
    """
    installer = DependencyInstaller(venv_path=venv_path)
    missing_packages = []
    
    # 检查核心依赖
    for package_name, version in installer.CORE_DEPENDENCIES.items():
        is_installed, _ = installer.check_package_installed(package_name)
        if not is_installed:
            missing_packages.append((package_name, version))
    
    if not missing_packages:
        logger.info("All core dependencies are installed")
        return True
    
    logger.info(f"Found {len(missing_packages)} missing dependencies")
    
    # 安装缺失的依赖
    success_count = 0
    for package_name, version in missing_packages:
        if installer.install_package(package_name, version):
            success_count += 1
    
    return success_count == len(missing_packages)