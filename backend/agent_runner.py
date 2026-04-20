import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _check_pdflatex():
    return shutil.which("pdflatex") is not None


def _build_prompt(course_name: str, material_paths: list[str], task_title: str,
                  task_description: str, task_file_paths: list[str]) -> str:
    material_list = "\n".join(f"- {p}" for p in material_paths) or "（无）"
    task_files_list = "\n".join(f"- {p}" for p in task_file_paths) or "（无）"

    return f"""你是一名专业的中国本科课程作业助手。请根据以下信息，用 LaTeX 完成这份作业，输出完整可编译的 .tex 文件内容。

# 课程名称
{course_name}

# 课程公共资料（文件路径，供参考）
{material_list}

# 本次作业标题
{task_title}

# 作业要求描述
{task_description}

# 上传的作业文件（文件路径，供参考）
{task_files_list}

# 输出要求
- 输出一个完整的、可直接用 pdflatex 编译的 LaTeX 文档
- 文档使用 ctexart 文档类支持中文
- 用 ```latex 和 ``` 包裹 LaTeX 代码块
- 不要有任何额外解释，只输出 LaTeX 代码块
"""


def _extract_latex(output: str) -> str | None:
    match = re.search(r"```latex\s*(.*?)```", output, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback: if output contains \documentclass directly
    if r"\documentclass" in output:
        start = output.index(r"\documentclass")
        return output[start:].strip()
    return None


def run_agent(task_id: int, course_name: str, material_paths: list[str],
              task_title: str, task_description: str, task_file_paths: list[str]) -> dict:
    prompt = _build_prompt(course_name, material_paths, task_title,
                           task_description, task_file_paths)

    # Call claude CLI
    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "text"],
        capture_output=True,
        text=True,
        timeout=300,
    )

    if result.returncode != 0:
        return {"ok": False, "error": result.stderr or "claude CLI failed"}

    latex_source = _extract_latex(result.stdout)
    if not latex_source:
        return {"ok": False, "error": "No LaTeX code found in claude output", "raw": result.stdout}

    if not _check_pdflatex():
        return {"ok": False, "error": "pdflatex not installed on server"}

    # Compile in temp dir
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "output.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_source)

        compile_result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "output.tex"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            timeout=120,
        )
        # Run twice for references
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "output.tex"],
            cwd=tmpdir,
            capture_output=True,
            timeout=120,
        )

        pdf_tmp = os.path.join(tmpdir, "output.pdf")
        if not os.path.exists(pdf_tmp):
            log = compile_result.stdout[-3000:] if compile_result.stdout else ""
            return {"ok": False, "error": f"pdflatex failed:\n{log}", "latex_source": latex_source}

        dest_pdf = os.path.join(OUTPUT_DIR, f"task_{task_id}.pdf")
        shutil.copy2(pdf_tmp, dest_pdf)

    return {"ok": True, "pdf_path": dest_pdf, "latex_source": latex_source}
