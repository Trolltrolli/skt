const REPO = 'Trolltrolli/skt';
const FILE = 'torrexplorer/seznam.html';
const BRANCH = 'main';
const ALLOWED_ORIGIN = 'https://trolltrolli.github.io';

function corsHeaders(origin) {
    return {
        'Access-Control-Allow-Origin':
            origin === ALLOWED_ORIGIN ? ALLOWED_ORIGIN : 'null',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '86400'
    };
}

function json(data, status, origin) {
    return new Response(JSON.stringify(data), {
        status,
        headers: {
            'Content-Type': 'application/json; charset=utf-8',
            ...corsHeaders(origin)
        }
    });
}

function bytesToBase64(bytes) {
    let binary = '';
    const chunk = 0x8000;

    for (let i = 0; i < bytes.length; i += chunk) {
        binary += String.fromCharCode(
            ...bytes.subarray(i, Math.min(i + chunk, bytes.length))
        );
    }

    return btoa(binary);
}

function textToBase64(text) {
    return bytesToBase64(
        new TextEncoder().encode(text)
    );
}

function base64ToText(base64) {
    const binary = atob(
        base64.replace(/\s/g, '')
    );

    const bytes = new Uint8Array(binary.length);

    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }

    return new TextDecoder().decode(bytes);
}

export default {
    async fetch(request, env) {

        const origin =
            request.headers.get('Origin') || '';

        if (request.method === 'OPTIONS') {
            return new Response(null, {
                status: 204,
                headers: corsHeaders(origin)
            });
        }

        if (origin !== ALLOWED_ORIGIN) {
            return json(
                {
                    ok: false,
                    error: 'Origin not allowed'
                },
                403,
                origin
            );
        }

        if (request.method !== 'POST') {
            return json(
                {
                    ok: false,
                    error: 'POST required'
                },
                405,
                origin
            );
        }

        try {

            const body =
                await request.json();

            const tbody =
                body?.tbody;

            if (
                typeof tbody !== 'string' ||
                !tbody.trim()
            ) {
                return json(
                    {
                        ok: false,
                        error: 'Missing TBODY'
                    },
                    400,
                    origin
                );
            }

            if (tbody.length > 5000000) {
                return json(
                    {
                        ok: false,
                        error: 'TBODY too large'
                    },
                    413,
                    origin
                );
            }

            const apiUrl =
                `https://api.github.com/repos/${REPO}/contents/${FILE}?ref=${BRANCH}`;

            const headers = {
                'Authorization':
                    `Bearer ${env.GITHUB_TOKEN}`,

                'Accept':
                    'application/vnd.github+json',

                'X-GitHub-Api-Version':
                    '2022-11-28',

                'User-Agent':
                    'Torrexplorer-Save-Worker'
            };

            // Načteme aktuální seznam.html
            const currentResponse =
                await fetch(apiUrl, {
                    method: 'GET',
                    headers
                });

            if (!currentResponse.ok) {

                const error =
                    await currentResponse.text();

                return json(
                    {
                        ok: false,
                        error: 'GitHub read failed',
                        details: error
                    },
                    502,
                    origin
                );
            }

            const current =
                await currentResponse.json();

            if (
                !current.sha ||
                !current.content
            ) {
                return json(
                    {
                        ok: false,
                        error:
                            'GitHub did not return file content or SHA'
                    },
                    502,
                    origin
                );
            }

            // Dekódujeme původní HTML
            const oldHtml =
                base64ToText(current.content);

            // Najdeme <tbody ...>
            const tbodyOpen =
                oldHtml.match(/<tbody\b[^>]*>/i);

            if (
                !tbodyOpen ||
                tbodyOpen.index === undefined
            ) {
                return json(
                    {
                        ok: false,
                        error:
                            'Existing seznam.html does not contain <tbody>'
                    },
                    500,
                    origin
                );
            }

            const tbodyStart =
                tbodyOpen.index +
                tbodyOpen[0].length;

            // Najdeme </tbody>
            const tbodyEnd =
                oldHtml.toLowerCase()
                    .indexOf(
                        '</tbody>',
                        tbodyStart
                    );

            if (tbodyEnd === -1) {
                return json(
                    {
                        ok: false,
                        error:
                            'Existing seznam.html does not contain </tbody>'
                    },
                    500,
                    origin
                );
            }

            // Nahradíme pouze obsah tbody
            const newHtml =
                oldHtml.slice(
                    0,
                    tbodyStart
                ) +
                tbody +
                oldHtml.slice(
                    tbodyEnd
                );

            // Zapíšeme celý výsledný seznam.html
            const updateResponse =
                await fetch(
                    `https://api.github.com/repos/${REPO}/contents/${FILE}`,
                    {
                        method: 'PUT',

                        headers: {
                            ...headers,
                            'Content-Type':
                                'application/json'
                        },

                        body: JSON.stringify({
                            message:
                                'Update seznam.html from Torrexplorer editor',

                            content:
                                textToBase64(newHtml),

                            sha:
                                current.sha,

                            branch:
                                BRANCH
                        })
                    }
                );

            const resultText =
                await updateResponse.text();

            if (!updateResponse.ok) {
                return json(
                    {
                        ok: false,
                        error: `GitHub write failed: ${resultText}`
                    },
                    502,
                    origin
                );
            }

            const result =
                JSON.parse(resultText);

            return json(
                {
                    ok: true,
                    commit:
                        result.commit?.sha || null,

                    message:
                        'seznam.html successfully saved'
                },
                200,
                origin
            );

        } catch (error) {

            return json(
                {
                    ok: false,
                    error:
                        error?.message ||
                        'Unknown error'
                },
                500,
                origin
            );
        }
    }
};