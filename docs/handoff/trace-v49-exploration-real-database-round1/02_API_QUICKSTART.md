# API quickstart

Base: `/api/trace/v1/exploration`. Start with `GET /api/trace/v1/exploration/categories`, then `POST /api/trace/v1/exploration/maps` using `{"category_id":"region","locale":"en","max_visible_nodes":40,"include_context":true,"include_spacetime":true}`. Pass each returned `state_hash` as the next action's `expected_state_hash`.
