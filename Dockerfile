FROM postgres:16-alpine

COPY database/init.sql /docker-entrypoint-initdb.d/01-init.sql

FROM python:3.11-slim