
import os
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class CppBatchCompiler:
    def __init__(self, compiler: str = "g++", output_dir: str = "build"):
        """
        初始化批量编译器
        
        Args:
            compiler: C++编译器 (g++, clang++, 等)
            output_dir: 输出目录
        """
        self.compiler = compiler
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 存储编译结果
        self.compilation_results = {}
        
    def check_compiler(self) -> bool:
        """检查编译器是否可用"""
        try:
            result = subprocess.run(
                [self.compiler, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def compile_single_file(self, source_file: str, output_name: str = None, 
                          flags: List[str] = None) -> Dict:
        """
        编译单个C++文件
        
        Args:
            source_file: 源文件路径
            output_name: 输出文件名
            flags: 编译选项
            
        Returns:
            编译结果字典
        """
        source_path = Path(source_file)
        if not source_path.exists():
            return {
                "success": False,
                "error": f"源文件不存在: {source_file}",
                "file": source_file
            }
        
        if output_name is None:
            output_name = source_path.stem
            
        if flags is None:
            flags = ["-std=c++17", "-Wall", "-Wextra"]
            
        output_path = self.output_dir / output_name
        
        # 添加.exe扩展名（Windows系统）
        if os.name == 'nt' and not output_path.suffix:
            output_path = output_path.with_suffix('.exe')
        
        compile_command = [self.compiler] + flags + [
            str(source_path),
            "-o", str(output_path)
        ]
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                compile_command,
                capture_output=True,
                text=True,
                timeout=60  # 60秒超时
            )
            
            end_time = time.time()
            compile_time = end_time - start_time
            
            compilation_result = {
                "success": result.returncode == 0,
                "file": source_file,
                "output": str(output_path),
                "compile_time": round(compile_time, 3),
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(compile_command)
            }
            
            if result.returncode != 0:
                compilation_result["error"] = f"编译失败，返回码: {result.returncode}"
                
        except subprocess.TimeoutExpired:
            compilation_result = {
                "success": False,
                "file": source_file,
                "error": "编译超时（60秒）",
                "compile_time": 60.0
            }
        except Exception as e:
            compilation_result = {
                "success": False,
                "file": source_file,
                "error": f"编译异常: {str(e)}"
            }
        
        self.compilation_results[source_file] = compilation_result
        return compilation_result
    
    def compile_directory(self, directory: str, pattern: str = "*.cpp",
                         recursive: bool = True) -> Dict[str, Dict]:
        """
        编译目录中的所有C++文件
        
        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            recursive: 是否递归搜索
            
        Returns:
            所有文件的编译结果
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return {"error": f"目录不存在: {directory}"}
        
        cpp_files = []
        if recursive:
            cpp_files = list(dir_path.rglob(pattern))
        else:
            cpp_files = list(dir_path.glob(pattern))
        
        results = {}
        for cpp_file in cpp_files:
            if cpp_file.is_file():
                result = self.compile_single_file(str(cpp_file))
                results[str(cpp_file)] = result
        
        return results
    
    def compile_file_list(self, file_list: List[str]) -> Dict[str, Dict]:
        """
        编译文件列表中的所有C++文件
        
        Args:
            file_list: C++文件路径列表
            
        Returns:
            所有文件的编译结果
        """
        results = {}
        for file_path in file_list:
            result = self.compile_single_file(file_path)
            results[file_path] = result
        
        return results
    
    def get_statistics(self) -> Dict:
        """获取编译统计信息"""
        if not self.compilation_results:
            return {}
        
        total = len(self.compilation_results)
        successful = sum(1 for result in self.compilation_results.values() 
                        if result.get("success", False))
        failed = total - successful
        
        total_time = sum(result.get("compile_time", 0) 
                        for result in self.compilation_results.values())
        
        return {
            "total_files": total,
            "successful": successful,
            "failed": failed,
            "success_rate": round(successful / total * 100, 2) if total > 0 else 0,
            "total_compile_time": round(total_time, 3),
            "average_compile_time": round(total_time / total, 3) if total > 0 else 0
        }
    
    def save_results(self, filename: str = None) -> str:
        """
        保存编译结果到JSON文件
        
        Args:
            filename: 输出文件名
            
        Returns:
            保存的文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"compilation_results_{timestamp}.json"
        
        output_file = self.output_dir / filename
        
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "compiler": self.compiler,
            "results": self.compilation_results,
            "statistics": self.get_statistics()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        return str(output_file)
    
    def print_summary(self):
        """打印编译摘要"""
        stats = self.get_statistics()
        
        print("\n" + "="*50)
        print("C++批量编译结果摘要")
        print("="*50)
        print(f"编译器: {self.compiler}")
        print(f"输出目录: {self.output_dir}")
        print(f"总文件数: {stats['total_files']}")
        print(f"成功: {stats['successful']}")
        print(f"失败: {stats['failed']}")
        print(f"成功率: {stats['success_rate']}%")
        print(f"总编译时间: {stats['total_compile_time']}秒")
        print(f"平均编译时间: {stats['average_compile_time']}秒")
        
        if stats['failed'] > 0:
            print("\n失败的文件:")
            for file_path, result in self.compilation_results.items():
                if not result.get("success", False):
                    error = result.get("error", "未知错误")
                    print(f"  - {file_path}: {error}")

def main():
    """使用示例"""
    # 创建编译器实例
    compiler = CppBatchCompiler(
        compiler="g++",  # 或者 "clang++"
        output_dir="build"
    )
    
    # 检查编译器
    if not compiler.check_compiler():
        print(f"错误: 编译器 {compiler.compiler} 不可用")
        return
    
    print(f"使用编译器: {compiler.compiler}")
    
    # 方法1: 编译单个文件
    print("\n1. 编译单个文件...")
    result = compiler.compile_single_file(
        "example.cpp",  # 替换为您的C++文件
        "my_program",
        flags=["-std=c++17", "-O2", "-Wall"]
    )
    
    if result["success"]:
        print(f"✓ 编译成功: {result['file']} -> {result['output']}")
    else:
        print(f"✗ 编译失败: {result['file']} - {result.get('error', '未知错误')}")
    
    # 方法2: 编译目录中的所有C++文件
    print("\n2. 编译目录中的文件...")
    directory_results = compiler.compile_directory(
        directory=".",        # 当前目录
        pattern="*.cpp",
        recursive=True        # 递归搜索子目录
    )
    
    # 方法3: 编译文件列表
    print("\n3. 编译文件列表...")
    file_list = [
        "program1.cpp",
        "program2.cpp",
        "program3.cpp"
    ]
    # 过滤掉不存在的文件
    existing_files = [f for f in file_list if Path(f).exists()]
    if existing_files:
        list_results = compiler.compile_file_list(existing_files)
    
    # 打印摘要
    compiler.print_summary()
    
    # 保存结果到文件
    results_file = compiler.save_results()
    print(f"\n详细结果已保存到: {results_file}")

if __name__ == "__main__":
    main()