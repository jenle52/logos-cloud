import os
import re
import json
import base64
import requests
from flask import Flask, render_template_string, request, redirect, url_for
from typing import Dict, Any, List

app = Flask(__name__)

# Облако Railway само подтянет сохраненный нами ранее ключ из настроек окружения
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "ЗАГЛУШКА")
DEEPSEEK_BASE_URL = "https://deepseek.com"

class LogosState:
    """Контур изолированной памяти агентов внутри облака."""
    def __init__(self):
        self._memory: Dict[str, str] = {}

    def set(self, key: str, value: Any):
        serialized = json.dumps(value)
        encoded = base64.b64encode(serialized.encode('utf-8')).decode('utf-8')
        self._memory[key] = encoded

    def get(self, key: str) -> Any:
        if key not in self._memory: return None
        decoded = base64.b64decode(self._memory[key].encode('utf-8')).decode('utf-8')
        return json.loads(decoded)

class LogosGraph:
    """Наш суверенный управляющий граф в облачной среде."""
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.conditional_edges = {}

    def add_node(self, name: str, func): self.nodes[name] = func
    def add_edge(self, start, end): self.edges[start] = end
    def add_conditional_edge(self, start, func): self.conditional_edges[start] = func

    def run(self, state: LogosState, start_node: str):
        current_node = start_node
        while current_node and current_node != "End":
            if current_node in self.nodes: state = self.nodes[current_node](state)
            if current_node in self.conditional_edges: current_node = self.conditional_edges[current_node](state)
            elif current_node in self.edges: current_node = self.edges[current_node]
            else: break
        return state

# Инициализируем наш суверенный ИИ-механизм
agent_graph = LogosGraph()

def agent_scout_cloud(state: LogosState) -> LogosState:
    """Облачной Разведчик: Автономно собирает реальные геополитические RSS-ленты."""
    texts = []
    feeds = ["https://reutersagency.com", "https://csis.org"]
    for url in feeds:
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
            items = re.findall(r'<item>(.*?)</item>', res.text, re.DOTALL)
            for item in items[:2]:
                title = re.search(r'<title>(.*?)</title>', item, re.DOTALL)
                desc = re.search(r'<description>(.*?)</description>', item, re.DOTALL)
                t_text = title.group(1) if title else ""
                d_text = desc.group(1) if desc else ""
                clean = re.sub('<[^<]+?>', '', f"{t_text}. {d_text}").strip()
                if len(clean) > 30: texts.append(clean)
        except Exception: pass
    if not texts:
        texts = ["Переговоры по ограничению цифрового суверенитета и введению фильтров информации нарастают на международных площадках под предлогом защиты свобод."]
    state.set("raw_batch", texts)
    return state

def agent_censor_cloud(state: LogosState) -> LogosState:
    """Облачной Цензор: Деконструирует софизмы и скрытую подмену понятий через DeepSeek."""
    batch = state.get("raw_batch")
    if "ЗАГЛУШКА" in DEEPSEEK_API_KEY:
        state.set("score", 0.5).set("swarm_index", 0.0).set("verdict", "Ключ не найден").set("essence", "Нет данных.")
        return state

    system_prompt = (
        "Вы — ядро ЛОГОС. Проанализируйте массив текстов на предмет софизма 'Скрытой подмены понятий' и ИИ-роев.\n"
        "Выдайте ответ строго в формате JSON без markdown разметки:\n"
        "{\n"
        '  "score": float, "swarm_index": float, "verdict": "короткая строка разбора софизма на русском", "essence": "чистая суть на русском"\n'
        "}"
    )
    formatted = "\n---\n".join(batch)
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": formatted}],
        "temperature": 0.1
    }
    try:
        # В облаке Railway этот запрос пройдет без блокировок CloudFront
        response = requests.post(DEEPSEEK_BASE_URL, headers=headers, json=payload, timeout=25)
        ai_msg = response.json()['choices']['message']['content'].strip()
        if "```" in ai_msg: ai_msg = re.sub(r"^```json|```$", "", ai_msg, flags=re.IGNORECASE).strip()
        analysis = json.loads(ai_msg)
        state.set("score", analysis.get("score", 0.4))
        state.set("swarm_index", analysis.get("swarm_index", 0.2))
        state.set("verdict", analysis.get("verdict", "Анализ завершен"))
        state.set("essence", analysis.get("essence", "Суть извлечена"))
    except Exception as e:
        state.set("score", 0.0).set("swarm_index", 1.0).set("verdict", f"Сбой API: {str(e)}").set("essence", "Сбой.")
    return state

agent_graph.add_node("Scout", agent_scout_cloud)
agent_graph.add_node("Censor", agent_censor_cloud)
agent_graph.add_edge("Scout", "Censor")

scanned_islands = {}

BASE_HTML = '<!DOCTYPE html><html><head><title>ЛОГОС Облако</title><style>body { font-family: monospace; background-color: #f4f1ea; color: #2b2a27; margin: 40px; } h1, h2 { color: #4a473e; border-bottom: 1px solid #8c8573; } .form-group { background: #faf8f5; padding: 20px; border: 1px solid #8c8573; text-align: center; } button { padding: 15px 30px; background: #4a473e; color: white; border: none; cursor: pointer; font-weight: bold; } .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; margin-top: 20px; } .card { padding: 20px; border: 1px solid #8c8573; background: #faf8f5; }</style></head><body><div class="container">{% block content %}{% endblock %}</div></body></html>'
INDEX_HTML = '{% extends "base" %}{% block content %}<h1>ЛОГОС v4.5: Суверенный Облачной Контур</h1><div class="form-group"><form action="/scan" method="post"><button type="submit">⚡ ЗАПУСТИТЬ АВТОНОМНЫЙ ГРАФ АГЕНТОВ</button></form></div><h2>Архипелаг проверенных островов чистоты</h2><div class="grid">{% for id, item in islands.items() %}<div class="card"><h3>Срез #{{ id }}</h3><p><strong>Логика (Aristotle Score):</strong> {{ item.score }}</p><p><strong>Анатомия софизма:</strong> {{ item.verdict }}</p><a href="/island/{{ id }}">Открыть ветку глубокого разбора &rarr;</a></div>{% endfor %}</div>{% endblock %}'
ISLAND_HTML = '{% extends "base" %}{% block content %;<a href="/">&larr; Вернуться к карте</a><h1>Разбор среза #{{ id }}</h1><p><strong>Aristotle Score:</strong> {{ item.score }} | <strong>Swarm Index:</strong> {{ item.swarm_index }}</p><h3>Анатомия обмана (Зафиксированная подмена понятий):</h3><div style="background: #fff; padding: 15px; border-left: 4px solid #4a473e; margin-bottom:20px;">{{ item.verdict }}</div><h3>Выделенная чистая суть реальности:</h3><div style="background: #faf8f5; padding: 15px; border: 1px solid #8c8573;">{{ item.essence }}</div>{% endblock %}'

@app.route('/')
def index(): return render_template_string(INDEX_HTML, islands=scanned_islands)

@app.route('/scan', methods=['POST'])
def scan():
    vault = LogosState()
    vault = agent_graph.run(vault, start_node="Scout")
    idx = str(len(scanned_islands) + 1)
    scanned_islands[idx] = {"score": vault.get("score"), "swarm_index": vault.get("swarm_index"), "verdict": vault.get("verdict"), "essence": vault.get("essence")}
    return redirect(url_for('index'))

@app.route('/island/<island_id>')
def island(island_id):
    item = scanned_islands.get(island_id)
    if not item: return "Не найдено", 404
    return render_template_string(ISLAND_HTML, id=island_id, item=item)

if __name__ == '__main__':
    import jinja2
    app.jinja_env.loader = jinja2.DictLoader({'base': BASE_HTML})
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

