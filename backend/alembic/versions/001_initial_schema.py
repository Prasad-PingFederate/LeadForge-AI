"""initial_schema

Revision ID: 001_initial
Revises: 
Create Date: 2026-11-22 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'campaigns',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('target_url', sa.String(length=512), nullable=False),
        sa.Column('campaign_type', sa.String(length=50), nullable=False, server_default='b2b'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icp_json', sa.Text(), nullable=True),
        sa.Column('deal_metadata_json', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'competitors',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('campaign_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('strengths', sa.Text(), nullable=True),
        sa.Column('weaknesses', sa.Text(), nullable=True),
        sa.Column('pricing_tier', sa.String(length=255), nullable=True),
        sa.Column('displacement_angle', sa.Text(), nullable=True),
        sa.Column('source_urls_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_competitor_campaign_id', 'competitors', ['campaign_id'], unique=False)

    op.create_table(
        'strategies',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('campaign_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('angle', sa.Text(), nullable=True),
        sa.Column('target_queries_json', sa.Text(), nullable=True),
        sa.Column('conversion_weight', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_strategy_campaign_id', 'strategies', ['campaign_id'], unique=False)

    op.create_table(
        'leads',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('campaign_id', sa.String(length=36), nullable=False),
        sa.Column('strategy_id', sa.String(length=36), nullable=True),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('contact_name', sa.String(length=255), nullable=True),
        sa.Column('contact_role', sa.String(length=255), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('email_status', sa.String(length=50), nullable=False),
        sa.Column('linkedin_url', sa.String(length=512), nullable=True),
        sa.Column('intent_platform', sa.String(length=50), nullable=False),
        sa.Column('intent_source_url', sa.String(length=1024), nullable=False),
        sa.Column('intent_snippet', sa.Text(), nullable=True),
        sa.Column('fit_score', sa.Integer(), nullable=False),
        sa.Column('intent_score', sa.Integer(), nullable=False),
        sa.Column('verif_score', sa.Integer(), nullable=False),
        sa.Column('overall_score', sa.Integer(), nullable=False),
        sa.Column('score_breakdown_json', sa.Text(), nullable=True),
        sa.Column('why_this_lead', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lead_campaign_id', 'leads', ['campaign_id'], unique=False)
    op.create_index('ix_lead_domain', 'leads', ['domain'], unique=False)
    op.create_index('ix_lead_contact_email', 'leads', ['contact_email'], unique=False)
    op.create_index('ix_lead_overall_score', 'leads', ['overall_score'], unique=False)

    op.create_table(
        'outreach_messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('lead_id', sa.String(length=36), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=True),
        sa.Column('body_step1', sa.Text(), nullable=True),
        sa.Column('body_step2', sa.Text(), nullable=True),
        sa.Column('body_step3', sa.Text(), nullable=True),
        sa.Column('social_reply', sa.Text(), nullable=True),
        sa.Column('linkedin_dm', sa.Text(), nullable=True),
        sa.Column('whatsapp_message', sa.Text(), nullable=True),
        sa.Column('telegram_message', sa.Text(), nullable=True),
        sa.Column('deal_affiliate_url', sa.String(length=1024), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reply_sentiment', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_outreach_lead_id', 'outreach_messages', ['lead_id'], unique=False)
    op.create_index('ix_outreach_status', 'outreach_messages', ['status'], unique=False)

    op.create_table(
        'suppression_list',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('reason', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_suppression_domain', 'suppression_list', ['domain'], unique=False)
    op.create_index('ix_suppression_email', 'suppression_list', ['email'], unique=False)


def downgrade() -> None:
    op.drop_table('suppression_list')
    op.drop_table('outreach_messages')
    op.drop_table('leads')
    op.drop_table('strategies')
    op.drop_table('competitors')
    op.drop_table('campaigns')
