import requests
import networkx as nx
import plotly.graph_objs as go
import plotly.offline as py

GITHUB_API_URL = "https://api.github.com"
GITHUB_SEARCH_REPOS_URL = f"{GITHUB_API_URL}/search/repositories"


def fetch_repositories(language="Python"):
    """Получение репозиториев из GitHub API."""
    query = f"language:{language}"
    params = {"q": query, "sort": "stars", "order": "desc", "per_page": 10}
    headers = {"Accept": "application/vnd.github.v3+json"}
    response = requests.get(GITHUB_SEARCH_REPOS_URL, headers=headers, params=params)
    response.raise_for_status()
    return response.json()["items"]


def fetch_dependencies(repo_full_name):
    """Получение зависимостей репозитория из файла requirements.txt."""
    repo_url = f"{GITHUB_API_URL}/repos/{repo_full_name}/contents/requirements.txt"
    headers = {"Accept": "application/vnd.github.v3+json"}
    response = requests.get(repo_url, headers=headers)
    if response.status_code == 200:
        content = response.json()
        if isinstance(content, dict) and content.get("encoding") == "base64":
            import base64
            requirements = base64.b64decode(content["content"]).decode("utf-8").splitlines()
            return requirements
    return []


def create_graph(repos):
    """Создание графа зависимостей репозиториев."""
    G = nx.DiGraph()
    for repo in repos:
        repo_name = repo["full_name"]
        repo_url = repo["html_url"]
        G.add_node(repo_name, url=repo_url, color="blue")
        dependencies = fetch_dependencies(repo_name)
        for dep in dependencies:
            dep_name = dep.split("==")[0].strip()
            G.add_node(dep_name, color="green")
            G.add_edge(repo_name, dep_name)
    return G


def draw_graph(graph):
    """Визуализация графа с помощью plotly."""
    pos = nx.spring_layout(graph)
    edge_trace = []

    for edge in graph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        trace = go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            line=dict(width=0.5, color="#888"),
            hoverinfo="none",
            mode="lines"
        )
        edge_trace.append(trace)

    node_trace = go.Scatter(
        x=[pos[node][0] for node in graph.nodes()],
        y=[pos[node][1] for node in graph.nodes()],
        text=[f'<a href="{graph.nodes[node]["url"]}">{node}</a>' if "url" in graph.nodes[node] else node for node in
              graph.nodes()],
        mode="markers+text",
        hoverinfo="text",
        marker=dict(
            showscale=False,
            color=[graph.nodes[node]["color"] for node in graph.nodes()],
            size=10,
            line_width=2
        )
    )

    fig = go.Figure(
        data=edge_trace + [node_trace],
        layout=go.Layout(
            title="GitHub Repositories and Dependencies",
            titlefont_size=16,
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[dict(
                text="GitHub Repositories on Python",
                showarrow=False,
                xref="paper",
                yref="paper"
            )],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
    )

    py.plot(fig, filename="github_graph.html")


def main():
    """Основная функция для получения данных и визуализации графа."""
    repos = fetch_repositories()
    graph = create_graph(repos)
    draw_graph(graph)


if __name__ == "__main__":
    main()
