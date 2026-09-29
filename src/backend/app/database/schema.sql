CREATE TABLE IF NOT EXISTS networks(
    id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    cidr TEXT,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS scans(
    id UUID PRIMARY KEY,
    network_id UUID NOT NULL REFERENCES networks(id) ON DELETE CASCADE,
    scan_datetime TIMESTAMPTZ DEFAULT NOW(),
    devices_found INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS devices (
    id UUID PRIMARY KEY,
    network_id UUID NOT NULL REFERENCES networks(id) ON DELETE CASCADE,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    mac_address MACADDR NOT NULL,
    ip_address INET NOT NULL,
    hostname TEXT,
    custom_name TEXT,
    status VARCHAR(16) NOT NULL DEFAULT 'ONLINE',
    first_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_network_mac UNIQUE (network_id, mac_address)
);

CREATE TABLE IF NOT EXISTS changes (
    id UUID PRIMARY KEY,
    device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE,
    change_type VARCHAR(32) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);