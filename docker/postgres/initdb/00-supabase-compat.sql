-- Supabase 互換の最低限エミュレーション（ローカル docker Postgres 専用）
--
-- 本番の Supabase には anon / authenticated / service_role ロールと
-- auth スキーマおよび auth.uid() 関数が既に存在するため、ローカル開発の
-- バニラ Postgres でも同じ DDL / RLS マイグレーションが通るように最低限を注入する。
--
-- このスクリプトは docker-compose.yml から /docker-entrypoint-initdb.d へマウントされ、
-- Postgres コンテナの **データディレクトリが空のとき** のみ自動実行される。
-- 既に pg-data ボリュームがある場合は `docker compose down -v` で消してから再起動すること。

-- ロールをべき等に作成
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'anon') THEN
        CREATE ROLE anon NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'authenticated') THEN
        CREATE ROLE authenticated NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'service_role') THEN
        CREATE ROLE service_role NOLOGIN BYPASSRLS;
    END IF;
END
$$;

-- auth スキーマを用意
CREATE SCHEMA IF NOT EXISTS auth;

-- auth.uid() のスタブ: セッション変数 request.jwt.claim.sub を uuid として返す
-- ローカルでは JWT を扱わないので通常は NULL を返す。
-- 必要なら `SET LOCAL request.jwt.claim.sub = '<uuid>';` で差し込めばポリシーの動作確認ができる。
CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid
LANGUAGE sql STABLE
AS $$
    SELECT NULLIF(current_setting('request.jwt.claim.sub', true), '')::uuid;
$$;

-- auth.role() / auth.jwt() もよく使われるので一応スタブ化
CREATE OR REPLACE FUNCTION auth.role() RETURNS text
LANGUAGE sql STABLE
AS $$
    SELECT NULLIF(current_setting('request.jwt.claim.role', true), '');
$$;

CREATE OR REPLACE FUNCTION auth.jwt() RETURNS jsonb
LANGUAGE sql STABLE
AS $$
    SELECT NULLIF(current_setting('request.jwt.claims', true), '')::jsonb;
$$;

-- スキーマ利用権限を付与
GRANT USAGE ON SCHEMA auth TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION auth.uid(), auth.role(), auth.jwt() TO anon, authenticated, service_role;
