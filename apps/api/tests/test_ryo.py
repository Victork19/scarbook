from app.ryo import _decode_mcp_response


def test_decode_mcp_tool_result_json_text():
    decoded = _decode_mcp_response({
        "jsonrpc": "2.0",
        "id": "scarbook-analyze_token",
        "result": {
            "content": [{
                "type": "text",
                "text": '{"status":"ok","data":{"verdict":"bullish","risk":"low"}}',
            }],
        },
    })
    assert decoded["data"]["verdict"] == "bullish"
    assert decoded["data"]["risk"] == "low"


def test_decode_mcp_error_becomes_unavailable():
    decoded = _decode_mcp_response({
        "jsonrpc": "2.0",
        "id": None,
        "error": {"code": -32600, "message": "Invalid JSON-RPC request"},
    })
    assert decoded["status"] == "error"
    assert decoded["data_mode"] == "unavailable"
