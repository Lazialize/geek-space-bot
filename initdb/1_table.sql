
CREATE TABLE IF NOT EXISTS reward (
    id BIGSERIAL PRIMARY KEY,
    hash_id TEXT NOT NULL,
    guild_id BIGINT NOT NULL,
    target_level INTEGER NOT NULL,
    reward_role_id BIGINT NOT NULL,
    UNIQUE(guild_id, target_level, reward_role_id),
    UNIQUE(guild_id, hash_id)
);

CREATE TABLE IF NOT EXISTS user_data (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    level BIGINT NOT NULL,
    own_exp BIGINT NOT NULL,
    next_exp BIGINT NOT NULL,
    total_exp BIGINT NOT NULL,
    last_message_timestamp TIMESTAMP,
    UNIQUE(guild_id, user_id),
    CHECK(own_exp < next_exp)
);

CREATE INDEX exp_rank ON user_data (total_exp DESC);
CREATE INDEX exp_rank_2 ON user_data (last_message_timestamp ASC);
