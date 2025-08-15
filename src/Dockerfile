FROM python:3.13-slim AS base

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID
ARG BUILD_CONTEXT=remote

ENV PYTHONDONTWRITEBYTECODE=1 \
   PYTHONUNBUFFERED=1 \
   PYTHONIOENCODING=utf-8 \
   LANG=C.UTF-8 \
   LC_ALL=C.UTF-8 \
   DEBIAN_FRONTEND=noninteractive \
   BUILD_CONTEXT=${BUILD_CONTEXT} 

RUN apt-get update && apt-get install -y --no-install-recommends \
   build-essential \
   curl \
   wget && \
   curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
   apt-get install -y nodejs && \
   node --version && \
   npm --version && \
   apt-get clean && rm -rf /var/lib/apt/lists/*

RUN if [ "$BUILD_CONTEXT" = "local" ] || [ "$BUILD_CONTEXT" = "devcontainer" ]; then \
   apt-get update && \
   apt-get install -y --no-install-recommends sudo graphviz && \
   npm install -g @devcontainers/cli && \
   devcontainer --version && \
   apt-get clean && rm -rf /var/lib/apt/lists/*; \
   fi

RUN pip install --no-cache-dir --upgrade pip build pipdeptree

# Application stage - builds on base and adds user + application
FROM base AS app

# Re-declare ARGs needed in this stage (ARGs don't carry over between stages)
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID
ARG BUILD_CONTEXT=remote

# Create non-root user
RUN groupadd --gid $USER_GID $USERNAME \
   && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
   && mkdir -p /etc/sudoers.d \
   && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
   && chmod 0440 /etc/sudoers.d/$USERNAME

# Optional SSH setup if devcontainer
RUN if [ "$BUILD_CONTEXT" = "devcontainer" ]; then \
   apt-get update && \
   apt-get install -y --no-install-recommends openssh-server && \
   mkdir -p /var/run/sshd && \
   mkdir -p /home/$USERNAME/.ssh && \
   chown -R $USERNAME:$USERNAME /home/$USERNAME/.ssh && \
   chmod 700 /home/$USERNAME/.ssh; \
   fi

WORKDIR /app
ENV PYTHONPATH="/app/scripts"

COPY ./scripts/11.5.3/requirements.txt ./scripts/11.5.3/
RUN pip install --no-cache-dir -r ./scripts/11.5.3/requirements.txt

COPY ./ ./

RUN chown -R $USERNAME:$USERNAME /app
USER $USERNAME

WORKDIR /app


