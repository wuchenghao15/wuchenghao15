#!/usr/bin/env python3
from flask import Blueprint, request, jsonify
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.learning_community import AILearningCommunity

community_api = Bluelogger.info('community_api', __name__)

@community_api.route('/api/community/posts', methods=['GET'])
def get_posts():
    """获取帖子列表"""
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    post_type = request.args.get('type')
    tag = request.args.get('tag')
    
    try:
        community = AILearningCommunity()
        posts = community.get_posts(page, page_size, post_type, tag)
        community.close()
        
        return jsonify({
            'success': True,
            'data': posts,
            'count': len(posts)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@community_api.route('/api/community/posts', methods=['POST'])
def create_post():
    """创建帖子"""
    data = request.get_json() or {}
    user_id = data.get('user_id', '1')
    title = data.get('title', '')
    content = data.get('content', '')
    post_type = data.get('post_type', 'discussion')
    tags = data.get('tags', [])
    
    if not title or not content:
        return jsonify({
            'success': False,
            'error': '标题和内容不能为空'
        }), 400
    
    try:
        community = AILearningCommunity()
        post_id = community.create_post(user_id, title, content, post_type, tags)
        community.close()
        
        return jsonify({
            'success': True,
            'post_id': post_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@community_api.route('/api/community/posts/<post_id>', methods=['GET'])
def get_post_detail(post_id):
    """获取帖子详情"""
    try:
        community = AILearningCommunity()
        post = community.get_post_detail(post_id)
        community.close()
        
        if not post:
            return jsonify({
                'success': False,
                'error': '帖子不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': post
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@community_api.route('/api/community/posts/<post_id>', methods=['DELETE'])
def delete_post(post_id):
    """删除帖子"""
    try:
        community = AILearningCommunity()
        result = community.delete_post(post_id)
        community.close()
        
        return jsonify({
            'success': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@community_api.route('/api/community/posts/<post_id>/comments', methods=['POST'])
def add_comment(post_id):
    """添加评论"""
    data = request.get_json() or {}
    user_id = data.get('user_id', '1')
    content = data.get('content', '')
    
    if not content:
        return jsonify({
            'success': False,
            'error': '评论内容不能为空'
        }), 400
    
    try:
        community = AILearningCommunity()
        comment_id = community.add_comment(post_id, user_id, content)
        community.close()
        
        return jsonify({
            'success': True,
            'comment_id': comment_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@community_api.route('/api/community/posts/<post_id>/likes', methods=['POST'])
def like_post(post_id):
    """点赞帖子"""
    data = request.get_json() or {}
    user_id = data.get('user_id', '1')
    
    try:
        community = AILearningCommunity()
        result = community.like_post(user_id, post_id)
        community.close()
        
        return jsonify({
            'success': True,
            'liked': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@community_api.route('/api/community/comments/<comment_id>/likes', methods=['POST'])
def like_comment(comment_id):
    """点赞评论"""
    data = request.get_json() or {}
    user_id = data.get('user_id', '1')
    
    try:
        community = AILearningCommunity()
        result = community.like_comment(user_id, comment_id)
        community.close()
        
        return jsonify({
            'success': True,
            'liked': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@community_api.route('/api/community/follow', methods=['POST'])
def follow_user():
    """关注用户"""
    data = request.get_json() or {}
    follower_id = data.get('follower_id', '1')
    following_id = data.get('following_id', '1')
    
    if follower_id == following_id:
        return jsonify({
            'success': False,
            'error': '不能关注自己'
        }), 400
    
    try:
        community = AILearningCommunity()
        result = community.follow_user(follower_id, following_id)
        community.close()
        
        return jsonify({
            'success': True,
            'followed': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@community_api.route('/api/community/unfollow', methods=['POST'])
def unfollow_user():
    """取消关注"""
    data = request.get_json() or {}
    follower_id = data.get('follower_id', '1')
    following_id = data.get('following_id', '1')
    
    try:
        community = AILearningCommunity()
        result = community.unfollow_user(follower_id, following_id)
        community.close()
        
        return jsonify({
            'success': True,
            'unfollowed': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@community_api.route('/api/community/users/<user_id>/following', methods=['GET'])
def get_following(user_id):
    """获取关注列表"""
    try:
        community = AILearningCommunity()
        following = community.get_following(user_id)
        community.close()
        
        return jsonify({
            'success': True,
            'data': following,
            'count': len(following)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@community_api.route('/api/community/users/<user_id>/followers', methods=['GET'])
def get_followers(user_id):
    """获取粉丝列表"""
    try:
        community = AILearningCommunity()
        followers = community.get_followers(user_id)
        community.close()
        
        return jsonify({
            'success': True,
            'data': followers,
            'count': len(followers)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@community_api.route('/api/community/tags', methods=['GET'])
def get_popular_tags():
    """获取热门标签"""
    limit = int(request.args.get('limit', 10))
    
    try:
        community = AILearningCommunity()
        tags = community.get_popular_tags(limit)
        community.close()
        
        return jsonify({
            'success': True,
            'data': tags,
            'count': len(tags)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@community_api.route('/api/community/search', methods=['GET'])
def search_posts():
    """搜索帖子"""
    keyword = request.args.get('keyword', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    
    if not keyword:
        return jsonify({
            'success': False,
            'error': '搜索关键词不能为空'
        }), 400
    
    try:
        community = AILearningCommunity()
        results = community.search_posts(keyword, page, page_size)
        community.close()
        
        return jsonify({
            'success': True,
            'data': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500