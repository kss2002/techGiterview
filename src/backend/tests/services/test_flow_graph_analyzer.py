
import pytest
import ast
from app.services.flow_graph_analyzer import FlowGraphAnalyzer, NodeType

class TestFlowGraphAnalyzer:
    def test_detects_fastapi_entry_points(self):
        analyzer = FlowGraphAnalyzer()
        content = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}
        """
        node_type = analyzer.determine_node_type("main.py", content)
        assert node_type == NodeType.ENTRY_POINT

    def test_detects_cli_entry_points(self):
        analyzer = FlowGraphAnalyzer()
        content = """
if __name__ == "__main__":
    main()
        """
        node_type = analyzer.determine_node_type("script.py", content)
        assert node_type == NodeType.ENTRY_POINT

    def test_scores_semantic_density_imperative(self):
        analyzer = FlowGraphAnalyzer()
        content = """
def complex_logic(x):
    if x > 10:
        return 1
    elif x < 5:
        return 0
    else:
        for i in range(x):
            try:
                process(i)
            except Exception:
                pass
    return -1
        """
        # 2 ifs + 1 loop + 1 try = 4 control structures
        # LOC approx 11
        density = analyzer.calculate_semantic_density(content)
        # 4 structures / 11 lines ~= 0.36
        assert density > 0.3

    def test_scores_semantic_density_declarative(self):
        analyzer = FlowGraphAnalyzer()
        # SQLAlchemy model
        content = """
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    created_at = Column(DateTime)
        """
        # 4 columns/fields
        density = analyzer.calculate_semantic_density(content)
        assert density > 0.2

    def test_scores_semantic_density_functional(self):
        analyzer = FlowGraphAnalyzer()
        content = """
def process_data(items):
    return list(map(lambda x: x*2, filter(lambda x: x>0, items)))
        """
        # map + filter
        density = analyzer.calculate_semantic_density(content)
        assert density > 0.2

    def test_low_density_boilerplate(self):
        analyzer = FlowGraphAnalyzer()
        content = """
def get_value(self):
    return self.value

def set_value(self, value):
    self.value = value
        """
        density = analyzer.calculate_semantic_density(content)
        # minimal logic
        assert density < 0.2
