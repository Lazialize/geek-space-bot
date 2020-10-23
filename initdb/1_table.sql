
CREATE TABLE IF NOT EXISTS reward (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT,
    target_level INTEGER NOT NULL,
    reward_role_id BIGINT NOT NULL,
    UNIQUE(guild_id, target_level, reward_role_id)
);

CREATE TABLE IF NOT EXISTS user_data (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    own_exp BIGINT NOT NULL,
    next_exp BIGINT NOT NULL,
    total_exp BIGINT NOT NULL,
    UNIQUE(guild_id, user_id),
    CHECK(own_exp < next_exp)
);