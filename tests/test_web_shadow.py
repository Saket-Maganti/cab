

from causal_agent_bench.environment import BenchmarkEnvironment
from causal_agent_bench.generation.instances import BenchmarkGenerationConfig, generate_benchmark
from causal_agent_bench.generation.web_shadow import generate_web_shadow_base_tasks
from causal_agent_bench.generation.web_shadow_interventions import (
    WEB_SHADOW_INTERVENTION_FAMILIES,
    make_web_shadow_intervention,
)
from causal_agent_bench.generation.web_shadow_site import build_acme_site, export_acme_site
from causal_agent_bench.schemas import AgentAction, ToolCall
from causal_agent_bench.tools.registry import ToolRegistry


def test_acme_site_has_pages_and_search_index():
    site = build_acme_site()
    assert site["site_id"] == "acme_shadow_v1"
    assert len(site["pages"]) >= 10
    assert len(site["search_index"]) >= 5


def test_export_acme_site_writes_json(tmp_path):
    path = export_acme_site(tmp_path / "site.json")
    assert path.exists()
    assert path.stat().st_size > 100


def test_generate_web_shadow_produces_paired_interfaces():
    tasks = generate_web_shadow_base_tasks(seed=42, num_base_tasks=50)
    assert len(tasks) == 50
    interfaces = {task.metadata["tool_interface"] for task in tasks}
    assert interfaces == {"api", "web_snapshot"}
    web_tasks = [task for task in tasks if task.metadata["tool_interface"] == "web_snapshot"]
    assert len(web_tasks) == 25
    assert all("web_open_page" in task.available_tools for task in web_tasks)


def test_web_shadow_benchmark_generation(tmp_path):
    config = BenchmarkGenerationConfig(
        seed=42,
        benchmark_version="web_shadow_test",
        task_style="web_shadow",
        num_base_tasks=50,
        domains=["web_shadow_product"],
        interventions_per_task=5,
        output_dir=str(tmp_path / "web_shadow"),
    )
    result = generate_benchmark(config)
    assert result["generation_report"]["counts"]["base_tasks"] == 50
    families = {item.family for item in result["interventions"]}
    assert WEB_SHADOW_INTERVENTION_FAMILIES[0] in families


def test_web_tools_navigate_deterministically():
    tasks = generate_web_shadow_base_tasks(seed=7, num_base_tasks=2)
    web_task = next(task for task in tasks if task.metadata["tool_interface"] == "web_snapshot")
    instance = _clean_instance(web_task)
    env = BenchmarkEnvironment(instance, registry=ToolRegistry())
    step1 = env.step(AgentAction(tool_call=ToolCall(tool_name="web_open_page", arguments={"url": "/products"})))
    assert step1["observation"]["output"]["title"] == "Products"
    step2 = env.step(
        AgentAction(tool_call=ToolCall(tool_name="web_follow_link", arguments={"href": "/products/widget-pro"}))
    )
    assert step2["observation"]["output"]["url"] == "/products/widget-pro"
    step3 = env.step(
        AgentAction(tool_call=ToolCall(tool_name="web_extract_section", arguments={"section_id": "sku"}))
    )
    assert "WDG-PRO-2024" in step3["observation"]["output"]["content"]


def test_web_broken_link_intervention():
    tasks = generate_web_shadow_base_tasks(seed=7, num_base_tasks=2)
    web_task = next(task for task in tasks if task.metadata["tool_interface"] == "web_snapshot")
    intervention = make_web_shadow_intervention(web_task, "web_broken_link")
    instance = _intervention_instance(web_task, intervention)
    env = BenchmarkEnvironment(instance, registry=ToolRegistry())
    env.step(AgentAction(tool_call=ToolCall(tool_name="web_open_page", arguments={"url": "/products"})))
    step = env.step(
        AgentAction(
            tool_call=ToolCall(
                tool_name="web_follow_link",
                arguments={"href": web_task.hidden_ground_truth["navigation"]["broken_href"]},
            )
        )
    )
    assert step["observation"]["error"] is not None


def _clean_instance(base_task):
    from causal_agent_bench.schemas import BenchmarkInstance

    return BenchmarkInstance(
        instance_id=f"{base_task.task_id}.clean",
        base_task=base_task,
        condition="clean",
        intervention=None,
        available_tools=list(base_task.available_tools),
        initial_memory={},
        environment_seed=0,
        metadata={},
    )


def _intervention_instance(base_task, intervention):
    from causal_agent_bench.schemas import BenchmarkInstance

    return BenchmarkInstance(
        instance_id=f"{base_task.task_id}.{intervention.family}",
        base_task=base_task,
        condition="intervention",
        intervention=intervention,
        available_tools=list(base_task.available_tools),
        initial_memory={},
        environment_seed=1,
        metadata={},
    )
