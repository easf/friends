CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER
VIEW `most_reactions` AS
    SELECT 
        `u`.`id` AS `po_fbid`,
        `u`.`idhash` AS `po_id`,
        `u`.`name` AS `post_owner`,
        `u2`.`id` AS `friend_fbid`,
        `u2`.`idhash` AS `friend_id`,
        `u2`.`name` AS `friend`,
        COUNT(`r`.`id`) AS `total_interactions`
    FROM
        ((((`user` `u`
        JOIN `profile` `p` ON ((`u`.`idhash` = `p`.`user_idhash`)))
        JOIN `postb` `pt` ON ((`p`.`user_idhash` = `pt`.`user_idhash`)))
        JOIN `reactionb` `r` ON ((`pt`.`id` = `r`.`post_id`)))
        JOIN `user` `u2` ON ((`r`.`user_idhash` = `u2`.`idhash`)))
    WHERE
        (`u`.`name` <> `u2`.`name`)
    GROUP BY `u`.`idhash` , `u2`.`idhash` , `u`.`name` , `u2`.`name` , `u`.`id` , `u2`.`id`
    ORDER BY `u`.`name` , COUNT(`r`.`id`) DESC;

    CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER
VIEW `most_comments` AS
    SELECT 
        `u`.`id` AS `po_fbid`,
        `u`.`idhash` AS `po_id`,
        `u`.`name` AS `post_owner`,
        `u2`.`id` AS `friend_fbid`,
        `u2`.`idhash` AS `friend_id`,
        `u2`.`name` AS `friend`,
        COUNT(`r`.`id`) AS `total_interactions`
    FROM
        ((((`user` `u`
        JOIN `profile` `p` ON ((`u`.`idhash` = `p`.`user_idhash`)))
        JOIN `postb` `pt` ON ((`p`.`user_idhash` = `pt`.`user_idhash`)))
        JOIN `commentb` `r` ON ((`pt`.`id` = `r`.`post_id`)))
        JOIN `user` `u2` ON ((`r`.`user_idhash` = `u2`.`idhash`)))
    WHERE
        (`u`.`name` <> `u2`.`name`)
    GROUP BY `u`.`idhash` , `u2`.`idhash` , `u`.`name` , `u2`.`name` , `u`.`id` , `u2`.`id`
    ORDER BY `u`.`name` , COUNT(`r`.`id`) DESC;

    CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER

VIEW `most_tagged` AS
    SELECT 
        `u`.`id` AS `po_fbid`,
        `u`.`idhash` AS `po_id`,
        `u`.`name` AS `post_owner`,
        `u2`.`id` AS `friend_fbid`,
        `u2`.`idhash` AS `friend_id`,
        `u2`.`name` AS `friend`,
        COUNT(`r`.`id`) AS `total_interactions`
    FROM
        ((((`user` `u`
        JOIN `profile` `p` ON ((`u`.`idhash` = `p`.`user_idhash`)))
        JOIN `postb` `pt` ON ((`p`.`user_idhash` = `pt`.`user_idhash`)))
        JOIN `tagb` `r` ON ((`pt`.`id` = `r`.`post_id`)))
        JOIN `user` `u2` ON ((`r`.`user_idhash` = `u2`.`idhash`)))
    WHERE
        (`u`.`name` <> `u2`.`name`)
    GROUP BY `u`.`idhash` , `u2`.`idhash` , `u`.`name` , `u2`.`name` , `u`.`id` , `u2`.`id`
    ORDER BY `u`.`name` , COUNT(`r`.`id`) DESC;

    CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER


VIEW `interactions_in_posts` AS
    SELECT 
        `most_reactions`.`po_fbid` AS `po_fbid`,
        `most_reactions`.`po_id` AS `po_id`,
        `most_reactions`.`post_owner` AS `post_owner`,
        `most_reactions`.`friend_fbid` AS `friend_fbid`,
        `most_reactions`.`friend_id` AS `friend_id`,
        `most_reactions`.`friend` AS `friend`,
        `most_reactions`.`total_interactions` AS `total_interactions`
    FROM
        `most_reactions` 
    UNION ALL SELECT 
        `most_comments`.`po_fbid` AS `po_fbid`,
        `most_comments`.`po_id` AS `po_id`,
        `most_comments`.`post_owner` AS `post_owner`,
        `most_comments`.`friend_fbid` AS `friend_fbid`,
        `most_comments`.`friend_id` AS `friend_id`,
        `most_comments`.`friend` AS `friend`,
        `most_comments`.`total_interactions` AS `total_interactions`
    FROM
        `most_comments` 
    UNION ALL SELECT 
        `most_tagged`.`po_fbid` AS `po_fbid`,
        `most_tagged`.`po_id` AS `po_id`,
        `most_tagged`.`post_owner` AS `post_owner`,
        `most_tagged`.`friend_fbid` AS `friend_fbid`,
        `most_tagged`.`friend_id` AS `friend_id`,
        `most_tagged`.`friend` AS `friend`,
        `most_tagged`.`total_interactions` AS `total_interactions`
    FROM
        `most_tagged`;

CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER
VIEW `interactions_in_posts_summary` AS
    SELECT 
        `interactions_in_posts`.`po_fbid` AS `po_fbid`,
        `interactions_in_posts`.`po_id` AS `po_id`,
        `interactions_in_posts`.`post_owner` AS `post_owner`,
        `interactions_in_posts`.`friend_fbid` AS `friend_fbid`,
        `interactions_in_posts`.`friend_id` AS `friend_id`,
        `interactions_in_posts`.`friend` AS `friend`,
        SUM(`interactions_in_posts`.`total_interactions`) AS `total_interaction`
    FROM
        `interactions_in_posts`
    GROUP BY `interactions_in_posts`.`po_fbid` , `interactions_in_posts`.`po_id` , `interactions_in_posts`.`post_owner` , `interactions_in_posts`.`friend_fbid` , `interactions_in_posts`.`friend` , `interactions_in_posts`.`friend_id`
    ORDER BY `interactions_in_posts`.`post_owner` , SUM(`interactions_in_posts`.`total_interactions`) DESC;

    CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER
VIEW `comments_replied_by_comment` AS
    SELECT 
        `u`.`id` AS `po_fbid`,
        `u`.`idhash` AS `po_id`,
        `u`.`name` AS `post_owner`,
        `u2`.`id` AS `friend_fbid`,
        `u2`.`idhash` AS `friend_id`,
        `u2`.`name` AS `friend`,
        COUNT(`r`.`id`) AS `total_interactions`
    FROM
        ((((((`user` `u`
        JOIN `profile` `p` ON ((`u`.`idhash` = `p`.`user_idhash`)))
        JOIN `postb` `pt` ON ((`p`.`user_idhash` = `pt`.`user_idhash`)))
        JOIN `commentb` `r` ON ((`pt`.`id` = `r`.`post_id`)))
        JOIN `user` `u2` ON ((`r`.`user_idhash` = `u2`.`idhash`)))
        JOIN `comment_has_comment` `c2` ON ((`r`.`id` = `c2`.`comment_id`)))
        JOIN `commentb` `c3` ON (((`c3`.`id` = `c2`.`comment_id1`)
            AND (`c3`.`user_idhash` = `u`.`idhash`))))
    WHERE
        (`u`.`name` <> `u2`.`name`)
    GROUP BY `u`.`idhash` , `u2`.`idhash` , `u`.`name` , `u2`.`name` , `u`.`id` , `u2`.`id`
    ORDER BY `u`.`name` , COUNT(`r`.`id`) DESC;

CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER
VIEW `comments_replied_by_reaction` AS
    SELECT 
        `u`.`id` AS `po_fbid`,
        `u`.`idhash` AS `po_id`,
        `u`.`name` AS `post_owner`,
        `u2`.`id` AS `friend_fbid`,
        `u2`.`idhash` AS `friend_id`,
        `u2`.`name` AS `friend`,
        COUNT(`r`.`id`) AS `total_interactions`
    FROM
        (((((`user` `u`
        JOIN `profile` `p` ON ((`u`.`idhash` = `p`.`user_idhash`)))
        JOIN `postb` `pt` ON ((`p`.`user_idhash` = `pt`.`user_idhash`)))
        JOIN `commentb` `r` ON ((`pt`.`id` = `r`.`post_id`)))
        JOIN `user` `u2` ON ((`r`.`user_idhash` = `u2`.`idhash`)))
        JOIN `reactionb` `r2` ON ((`r`.`id` = `r2`.`comment_id`)))
    WHERE
        ((`u`.`name` <> `u2`.`name`)
            AND (`r2`.`user_idhash` = `u`.`idhash`))
    GROUP BY `u`.`idhash` , `u2`.`idhash` , `u`.`name` , `u2`.`name` , `u`.`id` , `u2`.`id`
    ORDER BY `u`.`name` , COUNT(`r`.`id`) DESC;

CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER
VIEW `interactions_in_posts_replied` AS
    SELECT 
        `comments_replied_by_reaction`.`po_fbid` AS `po_fbid`,
        `comments_replied_by_reaction`.`po_id` AS `po_id`,
        `comments_replied_by_reaction`.`post_owner` AS `post_owner`,
        `comments_replied_by_reaction`.`friend_fbid` AS `friend_fbid`,
        `comments_replied_by_reaction`.`friend_id` AS `friend_id`,
        `comments_replied_by_reaction`.`friend` AS `friend`,
        `comments_replied_by_reaction`.`total_interactions` AS `total_interactions`
    FROM
        `comments_replied_by_reaction` 
    UNION ALL SELECT 
        `comments_replied_by_comment`.`po_fbid` AS `po_fbid`,
        `comments_replied_by_comment`.`po_id` AS `po_id`,
        `comments_replied_by_comment`.`post_owner` AS `post_owner`,
        `comments_replied_by_comment`.`friend_fbid` AS `friend_fbid`,
        `comments_replied_by_comment`.`friend_id` AS `friend_id`,
        `comments_replied_by_comment`.`friend` AS `friend`,
        `comments_replied_by_comment`.`total_interactions` AS `total_interactions`
    FROM
        `comments_replied_by_comment`;

CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER
VIEW `interactions_in_posts_replied_summary` AS
    SELECT 
        `interactions_in_posts_replied`.`po_fbid` AS `po_fbid`,
        `interactions_in_posts_replied`.`po_id` AS `po_id`,
        `interactions_in_posts_replied`.`post_owner` AS `post_owner`,
        `interactions_in_posts_replied`.`friend_fbid` AS `friend_fbid`,
        `interactions_in_posts_replied`.`friend_id` AS `friend_id`,
        `interactions_in_posts_replied`.`friend` AS `friend`,
        SUM(`interactions_in_posts_replied`.`total_interactions`) AS `total_interaction`
    FROM
        `interactions_in_posts_replied`
    GROUP BY `interactions_in_posts_replied`.`po_fbid` , `interactions_in_posts_replied`.`po_id` , `interactions_in_posts_replied`.`post_owner` , `interactions_in_posts_replied`.`friend_fbid` , `interactions_in_posts_replied`.`friend_id` , `interactions_in_posts_replied`.`friend`
    ORDER BY `interactions_in_posts_replied`.`post_owner` , SUM(`interactions_in_posts_replied`.`total_interactions`) DESC;

CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER
VIEW `ratio_amount_replied` AS
    SELECT 
        `amount`.`po_fbid` AS `po_fbid`,
        `amount`.`po_id` AS `po_id`,
        `amount`.`post_owner` AS `post_owner`,
        `amount`.`friend_fbid` AS `friend_fbid`,
        `amount`.`friend_id` AS `friend_id`,
        `amount`.`friend` AS `friend`,
        (`replied`.`total_interaction` / `amount`.`total_interaction`) AS `interaction_ratio`
    FROM
        (`interactions_in_posts_summary` `amount`
        JOIN `interactions_in_posts_replied_summary` `replied` ON ((`amount`.`friend_id` = `replied`.`friend_id`)))
    GROUP BY `amount`.`po_fbid` , `amount`.`po_id` , `amount`.`post_owner` , `amount`.`friend_fbid` , `amount`.`friend`
    ORDER BY `amount`.`post_owner` , (`replied`.`total_interaction` / `amount`.`total_interaction`) DESC;



